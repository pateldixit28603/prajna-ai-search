"""Tests for the daily digest + benchmark jobs (network and engine faked)."""
import datetime as dt
import json
from contextlib import asynccontextmanager

from app.nvidia import NvidiaClient
from app.pipeline import AnswerEngine
from app.runner import answer, citation_metrics
from conftest import DOCS, FakeSource, make_settings


def fake_session(tmp_path):
    s = make_settings(tmp_path)
    eng = AnswerEngine(s, NvidiaClient(s), {"wikipedia": FakeSource("wikipedia", DOCS)})

    @asynccontextmanager
    async def session():
        yield eng
    return session


async def test_runner_and_citation_metrics(tmp_path):
    async with fake_session(tmp_path)() as eng:
        r = await answer(eng, "When was Nvidia founded?", "wiki")
    m = citation_metrics(r)
    assert r["sources"] and "1993" in r["answer"]
    assert m["citation_coverage"] > 0.5 and m["citation_validity"] == 1.0 and m["faithfulness"] == 1.0


def test_citation_metrics_flags_bad_citations():
    r = {"answer": "Nvidia was founded on the Moon in 1850 [1]. It sells bananas to everyone today [7].",
         "sources": [{"n": 1}], "passages": {"1": ["Nvidia was founded in 1993 in California."]}}
    m = citation_metrics(r)
    assert m["citation_validity"] == 0.5 and m["faithfulness"] < 1.0


async def test_daily_digest_writes_outputs(tmp_path, monkeypatch):
    from scripts import daily_digest as dd

    async def fake_trending(day, counts):
        return [{"kind": "wikipedia", "topic": "Nvidia", "question": "When was Nvidia founded?",
                 "focus": "wiki", "context": "American technology company", "views": 123456,
                 "link": "https://en.wikipedia.org/wiki/Nvidia"},
                {"kind": "github", "topic": "acme/cuda-kit", "question": "What is CUDA?", "focus": "wiki",
                 "context": "Open-source CUDA helpers for GPUs", "stars": 4200, "language": "C++"}]

    monkeypatch.setattr(dd, "trending", fake_trending)
    monkeypatch.setattr(dd, "engine_session", fake_session(tmp_path))
    monkeypatch.setattr(dd, "DIGEST", tmp_path / "digest")
    monkeypatch.setattr(dd, "SITE", tmp_path / "site")
    monkeypatch.setattr(dd, "REPO", tmp_path)
    await dd.main_async(dt.date(2026, 11, 25), {"hn": 0, "github": 1, "papers": 0, "wiki": 1})

    data = json.loads((tmp_path / "digest/data/2026-11-25.json").read_text())
    assert data["items"][0]["result"]["sources"] and "passages" not in data["items"][0]["result"]
    assert data["categories_by"] == "keywords"            # fake engine has no NVIDIA key
    cats = {it["topic"]: it["category"] for it in data["items"]}
    assert cats == {"Nvidia": "chips", "acme/cuda-kit": "chips"}
    page = (tmp_path / "site/index.html").read_text()
    assert 'class="cite"' in page and "Prajna <span>Daily</span>" in page and "<script" not in page
    assert 'label for="f-chips">Chips &amp; Hardware <b>2</b>' in page and 'article class="c-chips"' in page
    assert "★ 4,200 GitHub stars · C++" in page and "123,456 Wikipedia views" in page
    md = (tmp_path / "DIGEST.md").read_text()
    assert "# Prajna Daily — 2026-11-25" in md and "## Chips & Hardware" in md


async def test_eval_report(tmp_path, monkeypatch):
    from eval import run_eval as ev
    monkeypatch.setattr(ev, "engine_session", fake_session(tmp_path))
    monkeypatch.setattr(ev, "ROOT", tmp_path)
    (tmp_path / "eval").mkdir()
    (tmp_path / "eval/questions.jsonl").write_text(
        json.dumps({"id": "nv", "question": "When was Nvidia founded?", "focus": "wiki", "expect": ["1993"]}) + "\n")
    result = await ev.run(None)
    assert result["summary"]["answer_accuracy"] == 1.0
    ev.write_reports(result, tmp_path / "EVAL.md")
    assert "| Answer accuracy | **100%**" in (tmp_path / "EVAL.md").read_text()
    assert (tmp_path / "eval/results/history.csv").read_text().count("\n") == 2
