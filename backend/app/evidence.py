"""Evidence view: for every [n] citation in an answer, find the exact passage text that supports it.

For each citation occurrence we take the cited sentence (the "claim"), look at the passages Prajna
actually retrieved from source n (already ranked by the NVIDIA reranker), pick the passage with the
most claim words in it, and mark the best-matching sentence inside that passage so the UI can
highlight it. Purely lexical and deterministic: no extra model call, so it is instant and free, and
it works even when NVIDIA is down.

Citations are keyed by (n, k): the k-th occurrence of [n] in the answer text (k starts at 0). That
key survives translation, because translations keep every [n] in the same order.
"""
from __future__ import annotations

import re

from .retrieval.text import tokenize

_CITE = re.compile(r"\[(\d{1,2})\]")
# split answer into sentences, keeping trailing "[n]" markers with their sentence
_ANS_SENT = re.compile(r"(?<=[.!?।。！？])\s+(?!\[\d)|\n+")
_PSG_SENT = re.compile(r"(?<=[.!?।。！？])\s+")
MAX_PASSAGE = 700


def _claim_sentences(answer: str) -> list[str]:
    return [s for s in _ANS_SENT.split(answer or "") if s and s.strip()]


def _best_span(passage: str, claim_terms: set[str]) -> tuple[int, int, float]:
    """(start, end, overlap) of the passage sentence sharing most words with the claim."""
    best = (0, 0, 0.0)
    pos = 0
    for sent in _PSG_SENT.split(passage):
        start = passage.find(sent, pos)
        if start < 0:
            continue
        pos = start + len(sent)
        toks = set(tokenize(sent))
        if not toks or not claim_terms:
            continue
        hit = len(toks & claim_terms) / len(claim_terms)
        if hit > best[2]:
            best = (start, start + len(sent), hit)
    return best


def _window(passage: str, start: int, end: int) -> tuple[str, int, int, bool, bool]:
    """Trim a long passage around the highlighted span. Returns text, new span and cut flags."""
    if len(passage) <= MAX_PASSAGE:
        return passage, start, end, False, False
    pad = max(0, (MAX_PASSAGE - (end - start)) // 2)
    a = max(0, start - pad)
    b = min(len(passage), max(end + pad, a + MAX_PASSAGE))
    if end - start > MAX_PASSAGE:
        b = start + MAX_PASSAGE
        end = b
    return passage[a:b], start - a, end - a, a > 0, b < len(passage)


def build_evidence(answer: str, passages_by_n: dict[int, list[str]]) -> list[dict]:
    """One evidence item per citation occurrence in the answer.

    passages_by_n: source number -> retrieved passage texts from that source (best first).
    """
    items: list[dict] = []
    seen: dict[int, int] = {}
    for sent in _claim_sentences(answer):
        claim = re.sub(r"\s*\[\d{1,2}\]", "", sent).strip()
        claim = re.sub(r"\s+([.,;:!?।。])", r"\1", claim)
        claim = re.sub(r"^\s*[-*]\s+|\*\*", "", claim).strip()
        terms = set(tokenize(claim))
        for m in _CITE.finditer(sent):
            n = int(m.group(1))
            k = seen.get(n, 0)
            seen[n] = k + 1
            cands = passages_by_n.get(n) or []
            if not cands:
                continue
            best_i, best = 0, (0, 0, 0.0)
            for i, p in enumerate(cands):
                span = _best_span(p, terms)
                if span[2] > best[2]:
                    best_i, best = i, span
            text, s, e, cut_l, cut_r = _window(cands[best_i], best[0], best[1])
            ptoks = set(tokenize(cands[best_i]))
            items.append({
                "n": n, "k": k, "claim": claim[:400], "passage": text,
                "highlight": [s, e] if best[2] > 0 else None,
                "overlap": round(best[2], 2),
                "matched": sorted(terms & ptoks)[:20],
                "cut_before": cut_l, "cut_after": cut_r,
            })
    return items


def passages_by_source(res) -> dict[int, list[str]]:
    """Group a SearchResult's (reranked) passages by public source number."""
    num = {d.id: i + 1 for i, d in enumerate(res.sources)}
    out: dict[int, list[str]] = {}
    for p in res.passages:
        n = num.get(p.doc.id)
        if n:
            out.setdefault(n, []).append(p.text)
    # sources with no retrieved passage still have their snippet/content as weak evidence
    for i, d in enumerate(res.sources, 1):
        if i not in out and (d.content or d.snippet):
            out[i] = [(d.content or d.snippet)[:2000]]
    return out
