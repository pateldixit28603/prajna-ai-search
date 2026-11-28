import asyncio

from fastapi.testclient import TestClient

from app.factcheck import decide, parse_stances, fact_check
from app.main import app
from app.nvidia import NvidiaClient
from app.pipeline import AnswerEngine
from app.store import ThreadStore
from conftest import DOCS, FakeSource, make_settings


def test_decide_rules():
    assert decide(["supports", "supports", "neutral"])["verdict"] == "supported"
    assert decide(["supports", "supports"])["confidence"] == "high"
    assert decide(["contradicts", "neutral"])["verdict"] == "contradicted"
    assert decide(["supports", "contradicts"])["verdict"] == "disputed"
    assert decide(["supports"] * 3 + ["contradicts"])["verdict"] == "supported"
    assert decide(["supports"] * 3 + ["contradicts"])["confidence"] == "medium"
    assert decide(["neutral", "neutral"])["verdict"] == "not_enough_evidence"
    assert decide(["unknown", "unknown"])["verdict"] == "unverified"
    d = decide(["supports", "contradicts", "contradicts", "neutral"])
    assert d["counts"] == {"supports": 1, "contradicts": 2, "neutral": 1} and d["agreement"] == 0.33


def test_parse_stances_is_defensive():
    raw = 'Sure! {"stances": [{"n": 1, "stance": "Supported", "reason": "x"}, {"n": "2", "stance": "refutes"},' \
          ' {"n": 7, "stance": "supports"}, {"n": 1, "stance": "contradicts"}, {"n": 3, "stance": "maybe"}],' \
          ' "summary": "See [1] and [7]."}'
    stances, summary = parse_stances(raw, 3)
    assert stances == {1: ("supports", "x"), 2: ("contradicts", "")}
    assert summary == "See [1] and ."
    assert parse_stances("no json here", 3) is None
    assert parse_stances('{"stances": []}', 3) is None


def test_fact_check_with_nim(online_nv):
    s, nv = online_nv
    engine = AnswerEngine(s, nv, {"wikipedia": FakeSource("wikipedia", DOCS)})
    out = asyncio.run(fact_check(engine, "Nvidia was founded in 1993", "wiki"))
    assert out["verdict"] == "supported" and out["nvidia"] and out["models"]["judge"] == s.llm_model
    sup = [e for e in out["evidence"] if e["stance"] == "supports"]
    assert sup and "1993" in sup[0]["passage"] and sup[0]["reason"] == "fake reason"
    assert all(e["stance"] in ("supports", "contradicts", "neutral") for e in out["evidence"])
    assert "[42]" not in out["summary"] and out["timings"]["total"] >= 0

    wrong = asyncio.run(fact_check(engine, "Nvidia was founded in 2001", "wiki"))
    assert wrong["verdict"] == "contradicted"
    assert wrong["counts"]["contradicts"] >= 1 and wrong["counts"]["supports"] == 0


def test_fact_check_without_nvidia_degrades(offline_nv):
    s, nv = offline_nv
    engine = AnswerEngine(s, nv, {"wikipedia": FakeSource("wikipedia", DOCS)})
    out = asyncio.run(fact_check(engine, "Nvidia was founded in 1993", "wiki"))
    assert out["verdict"] == "unverified" and not out["nvidia"]
    assert out["evidence"] and all(e["stance"] == "unknown" for e in out["evidence"])
    assert "could not judge" in out["summary"]


def test_factcheck_api(tmp_path):
    s = make_settings(tmp_path)
    app.state.engine = AnswerEngine(s, NvidiaClient(s), {"wikipedia": FakeSource("wikipedia", DOCS)})
    app.state.store = ThreadStore(tmp_path / "t.db")
    with TestClient(app) as c:
        assert "factcheck" in c.get("/api/health").json()["features"]
        r = c.post("/api/factcheck", json={"claim": "CUDA was created by Nvidia in 2006", "focus": "wiki"})
        assert r.status_code == 200
        j = r.json()
        assert j["claim"].startswith("CUDA") and j["label"] and j["evidence"][0]["url"].startswith("https://")
        assert c.post("/api/factcheck", json={"claim": "x"}).status_code == 422
        assert c.post("/api/factcheck", json={"claim": "valid claim", "focus": "nope"}).status_code == 400
