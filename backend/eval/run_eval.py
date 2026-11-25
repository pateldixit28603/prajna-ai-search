"""Prajna benchmark: runs the live pipeline over eval/questions.jsonl and writes EVAL.md.

Metrics per question
  answer_hit         all expected keywords present in the answer (case-insensitive)
  source_hit         expected keywords present in the retrieved sources' text
  citation_coverage  share of answer sentences that carry a [n] citation
  citation_validity  share of citations pointing at a real source
  faithfulness       share of cited sentences whose words are >=50% covered by the cited passages
  latency            end-to-end seconds

Usage:  python -m eval.run_eval [--limit N] [--out ../EVAL.md]
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import datetime as dt
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.runner import answer, citation_metrics, engine_session  # noqa: E402


def load(limit: int | None) -> list[dict]:
    rows = [json.loads(l) for l in (ROOT / "eval" / "questions.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    return rows[:limit] if limit else rows


def pct(x: float) -> str:
    return f"{100 * x:.0f}%"


def p95(xs: list[float]) -> float:
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(0.95 * (len(xs) - 1))))] if xs else 0.0


async def run(limit: int | None) -> dict:
    qs = load(limit)
    rows = []
    async with engine_session() as engine:
        for q in qs:
            try:
                r = await answer(engine, q["question"], q.get("focus", "all"))
            except Exception as e:  # keep benchmarking even if one question explodes
                rows.append({"id": q["id"], "error": f"{type(e).__name__}: {e}"[:200]})
                continue
            m = citation_metrics(r)
            ans = r["answer"].lower()
            src = " ".join(s["title"] + " " + s["snippet"] for s in r["sources"]).lower() + " " + \
                " ".join(" ".join(v) for v in r["passages"].values()).lower()
            exp = [e.lower() for e in q["expect"]]
            rows.append({
                "id": q["id"], "focus": q.get("focus", "all"), "question": q["question"],
                "answer_hit": all(e in ans for e in exp), "source_hit": all(e in src for e in exp),
                "n_sources": len(r["sources"]), "latency": r["timings"]["total"],
                "warnings": r["warnings"], "nvidia": r["nvidia"],
                "dense": bool(r["timings"].get("dense")), "rerank": bool(r["timings"].get("rerank")), **m,
            })
            print(f"  {q['id']:<20} answer={'✓' if rows[-1]['answer_hit'] else '✗'} "
                  f"src={'✓' if rows[-1]['source_hit'] else '✗'} cites={pct(m['citation_coverage'])} "
                  f"{r['timings']['total']:.1f}s", flush=True)
    ok = [r for r in rows if "error" not in r]
    mean = lambda k: statistics.mean(float(r[k]) for r in ok) if ok else 0.0  # noqa: E731
    lat = [r["latency"] for r in ok]
    summary = {
        "date": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "questions": len(rows), "errors": len(rows) - len(ok),
        "mode": (f"NVIDIA NIM ({sum(r['nvidia'] for r in ok)}/{len(ok)} answers by the LLM)"
                 if any(r["nvidia"] for r in ok) else "extractive (no NVIDIA LLM)"),
        "answer_accuracy": mean("answer_hit"), "retrieval_recall": mean("source_hit"),
        "citation_coverage": mean("citation_coverage"), "citation_validity": mean("citation_validity"),
        "faithfulness": mean("faithfulness"), "avg_sources": mean("n_sources"),
        "latency_p50": statistics.median(lat) if lat else 0.0, "latency_p95": p95(lat),
    }
    return {"summary": summary, "rows": rows}


def write_reports(result: dict, out_md: Path) -> None:
    s, rows = result["summary"], result["rows"]
    res_dir = ROOT / "eval" / "results"
    res_dir.mkdir(exist_ok=True)
    (res_dir / "latest.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    hist = res_dir / "history.csv"
    new = not hist.exists()
    with hist.open("a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["date", "mode", "questions", "answer_accuracy", "retrieval_recall", "citation_coverage",
                        "citation_validity", "faithfulness", "latency_p50", "latency_p95"])
        w.writerow([s["date"], s["mode"], s["questions"], *(f"{s[k]:.3f}" for k in
                    ["answer_accuracy", "retrieval_recall", "citation_coverage", "citation_validity",
                     "faithfulness", "latency_p50", "latency_p95"])])

    lines = [
        "# Prajna benchmark", "",
        f"_Last run: {s['date']} · mode: **{s['mode']}** · {s['questions']} questions · "
        "runs automatically every day via GitHub Actions._", "",
        "| Metric | Score | What it measures |", "|---|---|---|",
        f"| Answer accuracy | **{pct(s['answer_accuracy'])}** | expected facts appear in the answer |",
        f"| Retrieval recall | **{pct(s['retrieval_recall'])}** | expected facts appear in retrieved sources |",
        f"| Citation coverage | **{pct(s['citation_coverage'])}** | answer sentences carrying a [n] citation |",
        f"| Citation validity | **{pct(s['citation_validity'])}** | citations that point at a real source |",
        f"| Faithfulness (lexical) | **{pct(s['faithfulness'])}** | cited sentences supported by the cited passages |",
        f"| Latency p50 / p95 | **{s['latency_p50']:.1f}s / {s['latency_p95']:.1f}s** | end-to-end, incl. live API calls |",
        "", "## Per question", "",
        "| id | focus | answer | sources | cites | faithful | sources used | time |", "|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        if "error" in r:
            lines.append(f"| {r['id']} | – | ⚠️ {r['error'][:60]} | | | | | |")
            continue
        lines.append(f"| {r['id']} | {r['focus']} | {'✅' if r['answer_hit'] else '❌'} | "
                     f"{'✅' if r['source_hit'] else '❌'} | {pct(r['citation_coverage'])} | {pct(r['faithfulness'])} | "
                     f"{r['n_sources']} | {r['latency']:.1f}s |")
    lines += ["", "History: [`backend/eval/results/history.csv`](backend/eval/results/history.csv). "
              "Questions: [`backend/eval/questions.jsonl`](backend/eval/questions.jsonl)."]
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    ap.add_argument("--out", type=Path, default=ROOT.parent / "EVAL.md")
    args = ap.parse_args()
    result = asyncio.run(run(args.limit))
    write_reports(result, args.out)
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
