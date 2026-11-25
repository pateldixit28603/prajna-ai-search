"""Run the full answer pipeline outside the web server (used by eval + daily digest jobs)."""
from __future__ import annotations

import re
import time
from contextlib import asynccontextmanager

import httpx

from .retrieval.text import tokenize


@asynccontextmanager
async def engine_session():
    from .main import build_engine  # lazy: avoids starting the web app
    http = httpx.AsyncClient(follow_redirects=True, limits=httpx.Limits(max_connections=20))
    try:
        engine, _ = build_engine(http)
        yield engine
    finally:
        await http.aclose()
        await engine.nv.aclose()


async def answer(engine, question: str, focus: str = "all") -> dict:
    t0 = time.perf_counter()
    res = await engine.retrieve(question, focus, [])
    t_ret = time.perf_counter() - t0
    text = "".join([tok async for tok in engine.answer_stream(res, [])])
    text = engine.repair_citations(text, res)
    follow = await engine.followups(question, text, res)
    total = time.perf_counter() - t0
    by_n: dict[int, list[str]] = {}
    num = {d.id: i + 1 for i, d in enumerate(res.sources)}
    for p in res.passages:
        by_n.setdefault(num[p.doc.id], []).append(p.text)
    return {
        "question": question,
        "focus": focus,
        "queries": res.queries,
        "answer": text,
        "followups": follow,
        "sources": [d.to_public() | {"n": i + 1} for i, d in enumerate(res.sources)],
        "passages": {str(k): v for k, v in by_n.items()},
        "warnings": res.warnings,
        "timings": {**res.timings, "retrieve": t_ret, "total": total},
        "nvidia": bool(engine.nv.enabled and engine.last_llm_ok),
        "llm_error": "" if engine.last_llm_ok else getattr(engine, "last_llm_error", ""),
    }


_CITE = re.compile(r"\[(\d{1,2})\]")
# split after sentence punctuation, but keep a trailing "[n]" citation with its sentence
_SENT = re.compile(r"(?<=[.!?।])\s+(?!\[\d)|\n+")


def citation_metrics(result: dict) -> dict:
    """Citation coverage, validity and a lexical faithfulness proxy for one answer."""
    text = result["answer"].split("> _Extractive mode")[0]
    sents = [s.strip() for s in _SENT.split(text) if len(s.strip().split()) >= 5 and not s.strip().startswith("**")]
    n_sources = len(result["sources"])
    cited = valid = faithful = 0
    for s in sents:
        nums = [int(x) for x in _CITE.findall(s)]
        if not nums:
            continue
        cited += 1
        if all(1 <= n <= n_sources for n in nums):
            valid += 1
        claim = set(tokenize(_CITE.sub("", s)))
        support = set()
        for n in nums:
            for p in result["passages"].get(str(n), []):
                support |= set(tokenize(p))
        if claim and len(claim & support) / len(claim) >= 0.5:
            faithful += 1
    return {   # validity/faithfulness are undefined (None) when an answer has no citations at all
        "sentences": len(sents),
        "citation_coverage": cited / len(sents) if sents else 0.0,
        "citation_validity": valid / cited if cited else None,
        "faithfulness": faithful / cited if cited else None,
    }
