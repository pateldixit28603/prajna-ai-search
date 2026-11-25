import json

from fastapi.testclient import TestClient

from app.main import app
from app.pipeline import AnswerEngine
from app.store import ThreadStore
from conftest import FakeSource, DOCS, make_settings
from app.nvidia import NvidiaClient


def events(resp):
    return [json.loads(l[5:]) for l in resp.text.splitlines() if l.startswith("data:")]


def test_search_stream_and_threads(tmp_path):
    s = make_settings(tmp_path)
    app.state.engine = AnswerEngine(s, NvidiaClient(s), {"wikipedia": FakeSource("wikipedia", DOCS)})
    app.state.store = ThreadStore(tmp_path / "t.db")
    with TestClient(app) as c:
        assert c.get("/api/health").json()["status"] == "ok"
        r = c.post("/api/search", json={"query": "When was Nvidia founded?", "focus": "wiki"})
        ev = events(r)
        types = [e["type"] for e in ev]
        assert types[0] == "status" and "sources" in types and "token" in types and types[-1] == "done"
        sources = next(e for e in ev if e["type"] == "sources")["sources"]
        assert sources[0]["n"] == 1 and sources[0]["domain"] == "en.wikipedia.org" and "content" not in sources[0]
        tid = ev[-1]["thread_id"]

        # follow-up in same thread
        r2 = c.post("/api/search", json={"query": "What is CUDA?", "focus": "wiki", "thread_id": tid})
        assert events(r2)[-1]["thread_id"] == tid
        thread = c.get(f"/api/threads/{tid}").json()
        assert len(thread["turns"]) == 2 and "1993" in thread["turns"][0]["answer"]
        assert c.get("/api/threads").json()[0]["id"] == tid
        assert c.delete(f"/api/threads/{tid}").status_code == 200
        assert c.get(f"/api/threads/{tid}").status_code == 404

        assert c.post("/api/search", json={"query": "x", "focus": "nope"}).status_code == 400
        assert c.post("/api/search", json={"query": "", "focus": "all"}).status_code == 422
