"""Persistent local knowledge index (open datasets you ingest yourself).

Storage: data/index/chunks.jsonl  +  data/index/vectors.npy (NeMo Retriever embeddings).
Search : hybrid  = BM25 (lexical)  ⊕  cosine on NVIDIA embeddings (semantic), fused with RRF.
Scales comfortably to a few hundred thousand chunks on a laptop; swap in Milvus/cuVS for more.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np

from ..sources.base import Document
from .bm25 import BM25
from .fusion import argsort_desc, cosine, rrf

log = logging.getLogger("prajna.index")


class LocalIndex:
    name = "local"
    label = "Local index"

    def __init__(self, root: Path, embedder=None):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.embedder = embedder           # NvidiaClient or None
        self.chunks: list[dict] = []
        self.vectors: np.ndarray | None = None
        self._bm25: BM25 | None = None
        self.load()

    # ------------------------------------------------------------ persistence
    @property
    def chunks_path(self) -> Path:
        return self.root / "chunks.jsonl"

    @property
    def vectors_path(self) -> Path:
        return self.root / "vectors.npy"

    def load(self) -> None:
        self.chunks = []
        if self.chunks_path.exists():
            with self.chunks_path.open(encoding="utf-8") as f:
                self.chunks = [json.loads(line) for line in f if line.strip()]
        self.vectors = np.load(self.vectors_path) if self.vectors_path.exists() else None
        if self.vectors is not None and len(self.vectors) != len(self.chunks):
            log.warning("vector/chunk count mismatch — dense search disabled until re-ingest")
            self.vectors = None
        self._bm25 = BM25([c["text"] for c in self.chunks]) if self.chunks else None
        log.info("local index: %d chunks, dense=%s", len(self.chunks), self.vectors is not None)

    def add(self, chunks: list[dict], vectors: list[list[float]] | None) -> None:
        with self.chunks_path.open("a", encoding="utf-8") as f:
            for c in chunks:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
        if vectors is not None:
            new = np.asarray(vectors, dtype=np.float32)
            old = np.load(self.vectors_path) if self.vectors_path.exists() else None
            np.save(self.vectors_path, new if old is None else np.vstack([old, new]))
        self.load()

    def stats(self) -> dict:
        return {"chunks": len(self.chunks), "documents": len({c["url"] for c in self.chunks}),
                "dense": self.vectors is not None}

    # ----------------------------------------------------------------- search
    async def search(self, query: str, limit: int) -> list[Document]:
        if not self.chunks or self._bm25 is None:
            return []
        lexical = argsort_desc(self._bm25.scores(query))[:50]
        rankings = [lexical]
        if self.vectors is not None and self.embedder is not None and self.embedder.enabled:
            try:
                qv = (await self.embedder.embed([query], input_type="query"))[0]
                rankings.append(argsort_desc(cosine(qv, self.vectors))[:50])
            except Exception as e:  # network hiccup -> lexical only
                log.warning("dense search failed: %s", e)
        fused = sorted(rrf(rankings).items(), key=lambda kv: -kv[1])
        docs, seen = [], set()
        for idx, score in fused:
            c = self.chunks[idx]
            key = (c["url"], c["text"][:40])
            if key in seen:
                continue
            seen.add(key)
            docs.append(Document(title=c["title"], url=c["url"], content=c["text"], snippet=c["text"][:280],
                                 source="local", extra={"dataset": c.get("dataset", "local"), "rrf": round(score, 4)}))
            if len(docs) >= limit:
                break
        return docs
