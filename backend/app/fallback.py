"""Offline / no-key fallbacks so the engine still works without an NVIDIA key.

The extractive answerer picks the most query-relevant sentences from the top passages
and cites them — a mini "search snippet answer". Add NVIDIA_API_KEY to get full generative answers.
"""
from __future__ import annotations

import re

from .retrieval.text import tokenize

_SENT = re.compile(r"(?<=[.!?।])\s+")


def extractive_answer(question: str, passages: list[tuple[int, str]], max_sentences: int = 6) -> str:
    """passages: list of (citation_number, text)."""
    q = set(tokenize(question))
    scored: list[tuple[float, int, int, str]] = []
    for order, (num, text) in enumerate(passages):
        for j, s in enumerate(_SENT.split(text)):
            s = s.strip()
            if len(s.split()) < 6 or len(s) > 400:
                continue
            toks = set(tokenize(s))
            overlap = len(q & toks)
            if not overlap:
                continue
            score = overlap / (len(q) or 1) + 0.15 / (order + 1) + (0.05 if j == 0 else 0)
            scored.append((score, num, order, s))
    if not scored:
        return ("I couldn't find a direct answer in the retrieved sources. "
                "Try rephrasing, or open the sources below.")
    scored.sort(key=lambda x: -x[0])
    picked, seen = [], set()
    for score, num, order, s in scored:
        key = s[:60]
        if key in seen:
            continue
        seen.add(key)
        picked.append((order, num, s))
        if len(picked) >= max_sentences:
            break
    picked.sort(key=lambda x: x[0])
    lead = picked[0]
    body = [f"- {s} [{n}]" for _, n, s in picked[1:]]
    out = f"{lead[2]} [{lead[1]}]"
    if body:
        out += "\n\n**Key points from the sources:**\n" + "\n".join(body)
    out += ("\n\n> _Extractive mode: add an `NVIDIA_API_KEY` (or run a local NIM) "
            "for full AI-written answers._")
    return out


def heuristic_followups(question: str, titles: list[str]) -> list[str]:
    out = []
    for t in titles[:6]:
        cand = f"Tell me more about {t}"
        if t.lower() not in question.lower() and cand not in out:
            out.append(cand)
        if len(out) == 2:
            break
    out.append(f"What are the latest developments on {question.rstrip('?')}?")
    return out[:3]
