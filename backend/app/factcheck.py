"""Fact-check mode: paste a claim, get a verdict with the evidence for and against it.

   claim ──► the normal retrieval pipeline (Nemotron Bolt plans queries, open sources are searched,
             Embed 1B + Rerank 8B pick the most relevant passages)
         ──► Nemotron Lightning reads every passage and labels its stance on the claim
             (supports / contradicts / neutral) with a one-line reason
         ──► the verdict is computed here, in code, from those stances, so it is transparent and
             can't be talked into by the model: supported / contradicted / disputed / not enough evidence

If NVIDIA is unavailable (or the model reply is unusable), the most relevant passages are still
shown, and the verdict honestly says the claim could not be judged.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import time

from . import lang as L
from .evidence import _best_span, _window
from .retrieval.text import tokenize

log = logging.getLogger("prajna.factcheck")

MAX_EVIDENCE = 8
STANCES = ("supports", "contradicts", "neutral")
VERDICTS = {
    "supported": "Supported",
    "contradicted": "Contradicted",
    "disputed": "Disputed",
    "not_enough_evidence": "Not enough evidence",
    "unverified": "Could not verify",
}

FACTCHECK_SYSTEM = """You are a careful, neutral fact-checker.
You get a CLAIM and numbered EVIDENCE passages from open sources (Wikipedia, research papers, tech news).
For EACH passage decide its stance on the claim:
- "supports": the passage clearly states that the claim (or its key fact) is true.
- "contradicts": the passage clearly states something incompatible with the claim (a different date, number, person, place, or the opposite statement).
- "neutral": the passage is off-topic, about something else, or does not settle the claim.
Judge ONLY from the passages, never from your own knowledge. If unsure, use "neutral".
Return ONLY compact JSON, no commentary:
{"stances": [{"n": 1, "stance": "supports", "reason": "max 25 words: what the passage says"}], "summary": "2-3 sentences explaining what the evidence shows, citing passages as [n]"}
LANG_RULE"""


def _json_from(text: str) -> dict:
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return {}


def pick_evidence(res, limit: int = MAX_EVIDENCE) -> list[dict]:
    """Top reranked passages (already max 2 per source) as numbered evidence items."""
    num = {d.id: i + 1 for i, d in enumerate(res.sources)}
    items: list[dict] = []
    terms = set(tokenize(res.question))
    for p in res.passages[:limit]:
        a, b, hit = _best_span(p.text, terms)
        text, s, e, cut_l, cut_r = _window(p.text, a, b)
        pub = p.doc.to_public()
        items.append({
            "n": len(items) + 1, "source_n": num.get(p.doc.id), "title": p.doc.title, "url": p.doc.url,
            "domain": pub["domain"], "source": p.doc.source, "published": p.doc.published,
            "passage": text, "highlight": [s, e] if hit > 0 else None, "cut_before": cut_l, "cut_after": cut_r,
            "score": round(float(p.score), 3) if p.score not in (None, float("-inf")) else None,
            "stance": "unknown", "reason": "",
        })
    return items


def parse_stances(raw: str, n_items: int) -> tuple[dict[int, tuple[str, str]], str] | None:
    """Model reply -> ({n: (stance, reason)}, summary). None when the reply is unusable."""
    data = _json_from(raw)
    rows = data.get("stances")
    if not isinstance(rows, list):
        return None
    out: dict[int, tuple[str, str]] = {}
    for r in rows:
        if not isinstance(r, dict):
            continue
        try:
            n = int(r.get("n"))
        except (TypeError, ValueError):
            continue
        stance = str(r.get("stance", "")).strip().lower()
        stance = {"support": "supports", "supported": "supports", "contradict": "contradicts",
                  "contradicted": "contradicts", "refutes": "contradicts"}.get(stance, stance)
        if 1 <= n <= n_items and stance in STANCES and n not in out:
            out[n] = (stance, str(r.get("reason", "")).strip()[:300])
    if not out:
        return None
    summary = data.get("summary") if isinstance(data.get("summary"), str) else ""
    # drop citations to passages that don't exist
    summary = re.sub(r"\[(\d{1,2})\]", lambda m: m.group(0) if 1 <= int(m.group(1)) <= n_items else "", summary)
    return out, summary.strip()[:1200]


def decide(stances: list[str]) -> dict:
    """Verdict from passage stances. Deterministic, so the UI can explain exactly why."""
    s, c = stances.count("supports"), stances.count("contradicts")
    neutral = stances.count("neutral")
    if "unknown" in stances and not (s or c or neutral):
        verdict, conf = "unverified", "none"
    elif s == 0 and c == 0:
        verdict, conf = "not_enough_evidence", "low"
    elif c == 0 or s >= 3 * c:
        verdict = "supported"
        conf = "high" if s >= 2 and c == 0 else "medium"
    elif s == 0 or c >= 3 * s:
        verdict = "contradicted"
        conf = "high" if c >= 2 and s == 0 else "medium"
    else:
        verdict, conf = "disputed", "low"
    agreement = round(s / (s + c), 2) if s + c else None
    return {"verdict": verdict, "label": VERDICTS[verdict], "confidence": conf,
            "counts": {"supports": s, "contradicts": c, "neutral": neutral}, "agreement": agreement}


async def judge(engine, claim: str, items: list[dict], lang: str | None) -> tuple[str, str]:
    """Ask the NIM LLM for passage stances. Fills items in place. Returns (summary, model used or "")."""
    if not items or not engine.nv.enabled:
        return "", ""
    evidence = "\n\n".join(f"[{it['n']}] {it['title']} ({it['source']}{', ' + it['published'] if it['published'] else ''})\n"
                           f"{it['passage']}" for it in items)
    rule = L.language_instruction(lang).replace("whole answer", "reasons and the summary")
    messages = [{"role": "system", "content": FACTCHECK_SYSTEM.replace("LANG_RULE", rule)},
                {"role": "user", "content": f"CLAIM: {claim}\n\nEVIDENCE:\n{evidence}"}]
    s = engine.s
    models = [s.llm_model] + [m for m in [s.llm_backup_model] if m and m != s.llm_model]
    for model in models:
        try:
            raw = await asyncio.wait_for(engine.nv.chat(messages, model=model, temperature=0.0, max_tokens=900),
                                         timeout=40)
        except Exception as e:
            log.warning("fact-check judge failed on %s: %r", model, e)
            continue
        parsed = parse_stances(raw, len(items))
        if not parsed:
            log.warning("fact-check judge reply unusable on %s: %.200s", model, raw)
            continue
        stances, summary = parsed
        for it in items:
            it["stance"], it["reason"] = stances.get(it["n"], ("neutral", ""))
        return summary, model
    return "", ""


async def fact_check(engine, claim: str, focus: str = "all", lang: str | None = None) -> dict:
    t0 = time.perf_counter()
    lang = lang or L.detect_language(claim)
    res = await engine.retrieve(claim, focus, [], lang)
    items = pick_evidence(res)
    t1 = time.perf_counter()
    summary, model = await judge(engine, claim, items, lang)
    t2 = time.perf_counter()
    out = decide([it["stance"] for it in items])
    if not items:
        out |= {"verdict": "not_enough_evidence", "label": VERDICTS["not_enough_evidence"], "confidence": "low"}
        summary = "No relevant passages were found in the open sources. Try rephrasing the claim or another focus."
    elif not model:
        summary = ("Prajna found the passages below but could not judge them right now (the NVIDIA model "
                   "is unavailable). Read the evidence and decide for yourself.")
    return out | {
        "claim": claim, "lang": lang, "summary": summary, "evidence": items, "queries": res.queries,
        "sources": len(res.sources), "warnings": res.warnings, "nvidia": bool(model),
        "models": {"plan": engine.s.llm_fast_model if engine.nv.enabled else None,
                   "embed": engine.s.embed_model if res.timings.get("dense") else None,
                   "rerank": engine.s.rerank_model if res.timings.get("rerank") else None,
                   "judge": model or None},
        "timings": {k: round(v, 2) for k, v in res.timings.items() if k in ("plan", "search", "rank")}
                   | {"judge": round(t2 - t1, 2), "total": round(t2 - t0, 2)},
    }
