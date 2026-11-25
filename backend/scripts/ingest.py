"""Build the local open-data index (chunk -> NVIDIA NeMo Retriever embeddings -> data/index).

Examples
--------
# 1) Simple English Wikipedia dump from Hugging Face (open, CC BY-SA), first 5,000 articles
python -m scripts.ingest hf-wikipedia --config 20231101.simple --limit 5000

# 2) Full Wikipedia articles on chosen topics via the live API
python -m scripts.ingest wiki-titles "NVIDIA" "CUDA" "Transformer (deep learning architecture)"

# 3) Your own documents (.txt / .md / .jsonl with {"title","url","text"})
python -m scripts.ingest files ./my_docs

Embeddings are skipped automatically (BM25-only index) when no NVIDIA endpoint is configured.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings  # noqa: E402
from app.nvidia import NvidiaClient  # noqa: E402
from app.retrieval.local_index import LocalIndex  # noqa: E402
from app.retrieval.text import chunk_text  # noqa: E402

HF_PARQUET = "https://huggingface.co/datasets/wikimedia/wikipedia/resolve/main/{config}/train-00000-of-{n:05d}.parquet"


def to_chunks(title: str, url: str, text: str, dataset: str) -> list[dict]:
    return [{"title": title, "url": url, "text": c, "dataset": dataset}
            for c in chunk_text(text, settings.chunk_words, settings.chunk_overlap)]


async def write(index: LocalIndex, nv: NvidiaClient, chunks: list[dict], batch: int = 256) -> None:
    for i in range(0, len(chunks), batch):
        part = chunks[i:i + batch]
        vectors = None
        if nv.enabled and settings.use_dense:
            vectors = await nv.embed([f"{c['title']}. {c['text']}" for c in part], input_type="passage")
        index.add(part, vectors)
        print(f"  indexed {min(i + batch, len(chunks))}/{len(chunks)} chunks", flush=True)


# ---------------------------------------------------------------- sources
async def from_hf_wikipedia(config: str, limit: int, shards: int) -> list[dict]:
    try:
        import pyarrow.parquet as pq
    except ImportError:
        sys.exit("pip install pyarrow  (needed to read the Hugging Face parquet dump)")
    out: list[dict] = []
    cache = settings.data_dir / "raw"
    cache.mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient(follow_redirects=True, timeout=300) as c:
        url = HF_PARQUET.format(config=config, n=shards)
        dest = cache / f"{config}.parquet"
        if not dest.exists():
            print(f"downloading {url}")
            async with c.stream("GET", url) as r:
                r.raise_for_status()
                with dest.open("wb") as f:
                    async for b in r.aiter_bytes():
                        f.write(b)
    table = pq.read_table(dest, columns=["title", "url", "text"])
    for row in table.slice(0, limit).to_pylist():
        out.extend(to_chunks(row["title"], row["url"], row["text"][:20000], f"wikipedia:{config}"))
    return out


async def from_wiki_titles(titles: list[str], lang: str) -> list[dict]:
    out: list[dict] = []
    async with httpx.AsyncClient(timeout=30, headers={"User-Agent": settings.user_agent}) as c:
        for t in titles:
            r = await c.get(f"https://{lang}.wikipedia.org/w/api.php", params={
                "action": "query", "format": "json", "formatversion": "2", "prop": "extracts|info",
                "explaintext": "1", "inprop": "url", "titles": t, "redirects": "1"})
            for p in r.json()["query"]["pages"]:
                if p.get("missing"):
                    print(f"  ! not found: {t}")
                    continue
                out.extend(to_chunks(p["title"], p["fullurl"], p.get("extract", ""), f"wikipedia:{lang}"))
                print(f"  + {p['title']}")
    return out


def from_files(folder: Path) -> list[dict]:
    out: list[dict] = []
    for f in sorted(folder.rglob("*")):
        if f.suffix in {".txt", ".md"}:
            out.extend(to_chunks(f.stem.replace("_", " "), f.resolve().as_uri(), f.read_text(errors="ignore"), "files"))
        elif f.suffix == ".jsonl":
            for line in f.read_text(errors="ignore").splitlines():
                if line.strip():
                    d = json.loads(line)
                    out.extend(to_chunks(d.get("title", f.stem), d.get("url", f.resolve().as_uri()),
                                         d.get("text", ""), d.get("dataset", "files")))
    return out


async def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    h = sub.add_parser("hf-wikipedia")
    h.add_argument("--config", default="20231101.simple")
    h.add_argument("--limit", type=int, default=5000)
    h.add_argument("--shards", type=int, default=1, help="total parquet shards in that config")
    w = sub.add_parser("wiki-titles")
    w.add_argument("titles", nargs="+")
    w.add_argument("--lang", default="en")
    f = sub.add_parser("files")
    f.add_argument("folder", type=Path)
    sub.add_parser("stats")
    sub.add_parser("reset")
    args = ap.parse_args()

    nv = NvidiaClient(settings)
    index = LocalIndex(settings.data_dir / "index", embedder=nv)
    if args.cmd == "stats":
        print(index.stats())
        return
    if args.cmd == "reset":
        for p in (index.chunks_path, index.vectors_path):
            p.unlink(missing_ok=True)
        print("index cleared")
        return
    if args.cmd == "hf-wikipedia":
        chunks = await from_hf_wikipedia(args.config, args.limit, args.shards)
    elif args.cmd == "wiki-titles":
        chunks = await from_wiki_titles(args.titles, args.lang)
    else:
        chunks = from_files(args.folder)
    print(f"{len(chunks)} chunks to index (embeddings: {'NVIDIA ' + settings.embed_model if nv.enabled else 'off'})")
    await write(index, nv, chunks)
    print("done:", index.stats())
    await nv.aclose()


if __name__ == "__main__":
    asyncio.run(main())
