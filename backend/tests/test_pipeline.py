import pytest

from app.pipeline import AnswerEngine
from app.retrieval.local_index import LocalIndex
from conftest import BrokenSource, FakeSource


@pytest.mark.asyncio
async def test_offline_extractive_answer_with_citations(offline_nv, docs):
    s, nv = offline_nv
    eng = AnswerEngine(s, nv, {"wikipedia": FakeSource("wikipedia", docs), "arxiv": BrokenSource()})
    res = await eng.retrieve("When was Nvidia founded?", "all", [])
    assert res.queries == ["When was Nvidia founded?"]
    assert res.sources[0].title == "NVIDIA"
    assert any(w.startswith("arxiv") for w in res.warnings)          # broken source doesn't kill search
    answer = "".join([t async for t in eng.answer_stream(res, [])])
    assert "1993" in answer and "[1]" in answer
    fu = await eng.followups("When was Nvidia founded?", answer, res)
    assert len(fu) == 3


@pytest.mark.asyncio
async def test_nvidia_path_rewrite_dense_rerank_stream(online_nv, docs):
    s, nv = online_nv
    eng = AnswerEngine(s, nv, {"wikipedia": FakeSource("wikipedia", docs)})
    res = await eng.retrieve("When was Nvidia founded?", "wiki", [])
    assert res.queries == ["nvidia founding year"]                  # LLM query planning
    assert res.timings["dense"] == 1.0 and res.timings["rerank"] == 1.0
    assert "founded" in res.passages[0].text                         # reranker put the right passage first
    answer = "".join([t async for t in eng.answer_stream(res, [])])
    assert answer == "Nvidia was founded in 1993 [1]."               # <think> stripped
    assert (await eng.followups("q", answer, res))[0] == "Who founded Nvidia?"


@pytest.mark.asyncio
async def test_no_results_message(offline_nv):
    s, nv = offline_nv
    eng = AnswerEngine(s, nv, {"wikipedia": FakeSource("wikipedia", [])})
    res = await eng.retrieve("zzzz", "all", [])
    answer = "".join([t async for t in eng.answer_stream(res, [])])
    assert "couldn't find" in answer


@pytest.mark.asyncio
async def test_local_index_hybrid(online_nv, tmp_path):
    s, nv = online_nv
    idx = LocalIndex(tmp_path / "idx", embedder=nv)
    chunks = [{"title": "CUDA", "url": "u1", "text": "CUDA is Nvidia's GPU programming platform."},
              {"title": "Banana", "url": "u2", "text": "Banana is a fruit rich in potassium."}]
    vecs = await nv.embed([c["text"] for c in chunks])
    idx.add(chunks, vecs)
    assert idx.stats() == {"chunks": 2, "documents": 2, "dense": True}
    hits = await idx.search("cuda programming", 1)
    assert hits[0].title == "CUDA"
    # reload from disk
    assert LocalIndex(tmp_path / "idx").stats()["chunks"] == 2


async def test_repair_citations_only_when_supported(offline_nv, docs):
    s, nv = offline_nv
    eng = AnswerEngine(s, nv, {"wikipedia": FakeSource("wikipedia", docs)})
    res = await eng.retrieve("When was Nvidia founded?", "wiki", [])
    text = ("Nvidia was founded in 1993 by Jensen Huang, Chris Malachowsky and Curtis Priem. "
            "Purple elephants dance gracefully on distant frozen moons tonight.")
    out = eng.repair_citations(text, res)
    assert "Priem [1]." in out
    assert "moons tonight." in out and "tonight [" not in out
    assert eng.repair_citations("Already cited fact about Nvidia GPUs here [2].", res).count("[") == 1


async def test_repair_citations_skips_initials(offline_nv, docs):
    s, nv = offline_nv
    eng = AnswerEngine(s, nv, {"wikipedia": FakeSource("wikipedia", docs)})
    res = await eng.retrieve("When was Nvidia founded?", "wiki", [])
    out = eng.repair_citations("Nvidia was founded in 1993 by Jensen Huang and Chris A. Malachowsky with Curtis Priem.", res)
    assert "A. Malachowsky" in out and "A [" not in out
