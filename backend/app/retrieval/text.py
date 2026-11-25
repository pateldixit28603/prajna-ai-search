"""Tokenisation + chunking helpers shared by BM25 and the ingestion pipeline."""
from __future__ import annotations

import re
from dataclasses import dataclass

_TOKEN = re.compile(r"[\wऀ-ॿ]+", re.UNICODE)
_SENT = re.compile(r"(?<=[.!?।])\s+")

STOPWORDS = frozenset("""
a an and are as at be but by for from has have how i in is it its of on or that the this to was
what when where which who why will with you your do does did can could should would about into
than then there these those we they he she them our us me my not no yes if so very just also
kya hai ka ki ke ko me mein se aur ya hota hoti kaise kyu kyon kaun
""".split())


def tokenize(text: str) -> list[str]:
    return [t for t in (m.lower() for m in _TOKEN.findall(text)) if t not in STOPWORDS and len(t) > 1]


@dataclass
class Chunk:
    doc_index: int
    text: str
    position: int


def chunk_text(text: str, max_words: int = 180, overlap: int = 40) -> list[str]:
    """Sentence-aware sliding window chunker."""
    sentences = [s.strip() for s in _SENT.split(text) if s.strip()]
    chunks: list[str] = []
    cur: list[str] = []
    cur_len = 0
    for s in sentences:
        n = len(s.split())
        if n > max_words:  # very long sentence: hard split
            words = s.split()
            for i in range(0, len(words), max_words - overlap):
                piece = " ".join(words[i:i + max_words])
                if cur:
                    chunks.append(" ".join(cur))
                    cur, cur_len = [], 0
                chunks.append(piece)
            continue
        if cur_len + n > max_words and cur:
            chunks.append(" ".join(cur))
            # carry overlap
            tail: list[str] = []
            tl = 0
            for prev in reversed(cur):
                tl += len(prev.split())
                tail.insert(0, prev)
                if tl >= overlap:
                    break
            cur, cur_len = tail, sum(len(x.split()) for x in tail)
        cur.append(s)
        cur_len += n
    if cur:
        chunks.append(" ".join(cur))
    # de-duplicate tiny trailing chunks
    return [c for i, c in enumerate(chunks) if i == 0 or len(c.split()) >= 12]
