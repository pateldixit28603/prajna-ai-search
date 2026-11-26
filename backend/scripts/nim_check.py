"""Check every configured NVIDIA endpoint and record which ones work (never prints the key).

Writes backend/eval/results/nim_status.json and exits 0 even on failure so the daily job continues.
If the configured answer model fails, it also probes a few fallback chat models and reports which work.
"""
from __future__ import annotations

import asyncio
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import settings  # noqa: E402
from app.nvidia import NvidiaClient  # noqa: E402

FALLBACK_CHAT = [
    "meta/llama-3.3-70b-instruct",
    "meta/llama-3.1-8b-instruct",
    "nvidia/llama-3.3-nemotron-super-49b-v1.5",
    "nvidia/nvidia-nemotron-nano-9b-v2",
    "nvidia/llama-3.1-nemotron-nano-8b-v1",
    "mistralai/mistral-small-24b-instruct",
]


async def probe(name: str, coro) -> dict:
    try:
        out = await asyncio.wait_for(coro, timeout=45)
        return {"check": name, "ok": True, "detail": str(out)[:80]}
    except Exception as e:
        return {"check": name, "ok": False, "detail": f"{type(e).__name__}: {str(e)[:220]}"}


async def main() -> None:
    nv = NvidiaClient(settings)
    msg = [{"role": "user", "content": "Reply with the single word: ready"}]
    results = [
        await probe(f"chat:{settings.llm_model}", nv.chat(msg, max_tokens=400)),
        await probe(f"chat:{settings.llm_fast_model}", nv.chat(msg, model=settings.llm_fast_model, max_tokens=400)),
        await probe(f"embed:{settings.embed_model}", nv.embed(["hello world"], input_type="query")),
        await probe(f"rerank:{settings.rerank_model}", nv.rerank("gpu", ["CUDA runs on GPUs", "bananas"])),
    ]
    # discover what the catalog currently serves (models get retired regularly)
    catalog: list[str] = []
    try:
        r = await nv._client.get(f"{settings.llm_base_url}/models", headers=nv._headers())
        catalog = sorted(m["id"] for m in r.json().get("data", []))
    except Exception as e:
        results.append({"check": "list-models", "ok": False, "detail": str(e)[:200]})
    if not results[0]["ok"] or not results[1]["ok"]:
        cands = [m for m in catalog if "nemotron" in m and not any(x in m for x in
                 ("embed", "rerank", "guard", "safety", "parse", "reward", "vl", "omni", "retriever", "ocr"))]
        for m in (cands[-6:] + [m for m in FALLBACK_CHAT if m in catalog])[:10]:
            results.append(await probe(f"chat:{m}", nv.chat(msg, model=m, max_tokens=400)))
    if not results[2]["ok"]:
        for m in [m for m in catalog if "embed" in m][:6]:
            async def emb(model=m):
                payload = {"model": model, "input": ["hello"], "input_type": "query", "encoding_format": "float"}
                r = await nv._client.post(f"{settings.embed_base_url}/embeddings", headers=nv._headers(), json=payload)
                r.raise_for_status()
                return len(r.json()["data"][0]["embedding"])
            results.append(await probe(f"embed:{m}", emb()))
    if not results[3]["ok"]:
        rr_cands = ["nvidia/nemotron-3.5-rerank-8b", "nvidia/llama-nemotron-rerank-1b-v2",
                    "nvidia/llama-3.2-nemoretriever-500m-rerank-v2"]
        for m in dict.fromkeys(rr_cands + [m for m in catalog if "rerank" in m]):
            slug = m.split("/", 1)[1].replace(".", "_")
            for url in (f"https://ai.api.nvidia.com/v1/retrieval/nvidia/{slug}/reranking",
                        f"https://ai.api.nvidia.com/v1/retrieval/{m}/reranking"):
                async def rr(model=m, url=url):
                    r = await nv._client.post(url, headers=nv._headers(), json={
                        "model": model, "query": {"text": "gpu"}, "passages": [{"text": "CUDA runs on GPUs"}]})
                    r.raise_for_status()
                    return r.json()["rankings"][0]
                results.append(await probe(f"rerank:{m} @ {url}", rr()))
    # image generation: one small FLUX schnell render per day tells us which visual-GenAI model works
    from app.imagegen import ImageGenerator
    ig = ImageGenerator(settings)
    async def img():
        out = await ig.generate("a small green circuit board, studio photo", "square", seed=7)
        return f"{out['model']} ok ({len(out['image']) // 1365} KB)"
    results.append(await probe("image:" + ",".join(settings.image_models), img()))
    if ig.dead:
        results.append({"check": "image:unavailable", "ok": False, "detail": ", ".join(sorted(ig.dead))})
    await ig.aclose()
    # Research mode data source (not NVIDIA, but checked here so the daily status shows it)
    import httpx
    from app.research import ResearchService
    async with httpx.AsyncClient(follow_redirects=True) as http:
        rs = ResearchService(http, settings.user_agent, settings.contact_email)
        async def research():
            r = await rs.explore("retrieval augmented generation")
            return (f"{len(r['key_papers'])} key, {len(r['read_next'])} read-next, "
                    f"{len(r['timeline'])} years, warnings={r['warnings']}")
        results.append(await probe("research:openalex", research()))
    await nv.aclose()
    status = {"date": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
              "key_present": bool(settings.nvidia_api_key), "results": results, "catalog": catalog}
    out = ROOT / "eval" / "results" / "nim_status.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(status, indent=2), encoding="utf-8")
    for r in results:
        print(("OK  " if r["ok"] else "FAIL"), r["check"], "-", r["detail"])


if __name__ == "__main__":
    asyncio.run(main())
