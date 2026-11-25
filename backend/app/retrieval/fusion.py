"""Rank fusion + vector maths."""
from __future__ import annotations

import numpy as np


def rrf(rankings: list[list[int]], k: int = 60) -> dict[int, float]:
    """Reciprocal Rank Fusion: combine several ranked lists of item ids."""
    fused: dict[int, float] = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking):
            fused[item] = fused.get(item, 0.0) + 1.0 / (k + rank + 1)
    return fused


def argsort_desc(scores: list[float] | np.ndarray) -> list[int]:
    return [int(i) for i in np.argsort(-np.asarray(scores, dtype=float), kind="stable")]


def cosine(query: list[float], matrix: np.ndarray) -> np.ndarray:
    q = np.asarray(query, dtype=np.float32)
    q = q / (np.linalg.norm(q) or 1.0)
    m = matrix / np.clip(np.linalg.norm(matrix, axis=1, keepdims=True), 1e-9, None)
    return m @ q


def mmr(query_vec: list[float], doc_vecs: np.ndarray, candidates: list[int], k: int, lam: float = 0.75) -> list[int]:
    """Maximal Marginal Relevance — keeps results relevant *and* diverse."""
    if not candidates:
        return []
    sims = cosine(query_vec, doc_vecs)
    norm = doc_vecs / np.clip(np.linalg.norm(doc_vecs, axis=1, keepdims=True), 1e-9, None)
    chosen: list[int] = []
    pool = list(candidates)
    while pool and len(chosen) < k:
        best, best_score = pool[0], -1e9
        for c in pool:
            redundancy = max((float(norm[c] @ norm[j]) for j in chosen), default=0.0)
            score = lam * float(sims[c]) - (1 - lam) * redundancy
            if score > best_score:
                best, best_score = c, score
        chosen.append(best)
        pool.remove(best)
    return chosen
