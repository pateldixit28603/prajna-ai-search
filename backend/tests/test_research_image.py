import base64
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app import research as R
from app.imagegen import ImageError, ImageGenerator, build_body, mime_of, parse_image
from app.main import app
from app.nvidia import NvidiaClient
from app.pipeline import AnswerEngine
from app.research import ResearchService
from app.store import ThreadStore
from conftest import DOCS, FakeSource, make_settings, nim_transport


def work(wid, title, year, cites, related=()):
    return {"id": f"https://openalex.org/{wid}", "title": title, "publication_year": year, "cited_by_count": cites,
            "doi": f"https://doi.org/10.1/{wid}", "authorships": [{"author": {"display_name": f"A{i}"}} for i in range(5)],
            "primary_location": {"source": {"display_name": "NeurIPS"}},
            "open_access": {"is_oa": True, "oa_url": f"https://arxiv.org/abs/{wid}"},
            "related_works": [f"https://openalex.org/{r}" for r in related],
            "abstract_inverted_index": {"Retrieval": [0], "helps": [1], "LLMs": [2]}}


def openalex_transport(calls):
    def handler(req: httpx.Request):
        q = dict(req.url.params)
        calls.append(q)
        if "group_by" in q:
            return httpx.Response(200, json={"group_by": [
                {"key": "2019", "count": 3}, {"key": "2021", "count": 40}, {"key": "2023", "count": 900},
                {"key": "2099", "count": 5}, {"key": "unknown", "count": 1}]})
        if q.get("filter", "").startswith("ids.openalex:"):
            ids = q["filter"].split(":", 1)[1].split("|")
            return httpx.Response(200, json={"results": [work(i, f"Related {i}", 2022, 50) for i in reversed(ids)]})
        if q.get("filter", "").startswith("from_publication_date"):
            return httpx.Response(200, json={"results": [work("W9", "Rising RAG", 2025, 300), work("W1", "dup", 2025, 1)]})
        if q.get("sort") == "cited_by_count:desc":
            return httpx.Response(200, json={"results": [work("W5", "Dense Passage Retrieval", 2020, 5000)]})
        return httpx.Response(200, json={"meta": {"count": 12345}, "results": [
            work("W1", "RAG for knowledge-intensive NLP", 2020, 4000, related=("W7", "W8", "W5")),
            work("W2", "Self-RAG", 2023, 800, related=("W7", "W6")),
        ]})
    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_research_explore_builds_literature_map():
    calls = []
    async with httpx.AsyncClient(transport=openalex_transport(calls)) as http:
        svc = ResearchService(http, "test-agent", "me@example.com")
        r = await svc.explore("retrieval augmented generation")
        assert r["total_works"] == 12345 and [p["id"] for p in r["key_papers"]] == ["W1", "W2"]
        p = r["key_papers"][0]
        assert p["cited_by"] == 4000 and p["authors"][-1] == "et al." and p["oa_url"] and p["abstract"] == "Retrieval helps LLMs"
        assert [p["id"] for p in r["foundational"]] == ["W5"]
        assert [p["id"] for p in r["rising"]] == ["W9"]          # W1 already shown, de-duplicated
        assert [p["id"] for p in r["read_next"]][0] == "W7"         # related to both top papers ranks first
        assert "W5" not in [p["id"] for p in r["read_next"]]
        years = [t["year"] for t in r["timeline"]]
        assert years == list(range(2019, 2024)) and r["peak_year"] == 2023   # gaps filled, future dropped
        assert all(c.get("mailto") == "me@example.com" for c in calls)
        n = len(calls)
        await svc.explore("Retrieval augmented generation ")          # cached
        assert len(calls) == n


@pytest.mark.asyncio
async def test_research_degrades_and_raises_when_all_down():
    def down(req):
        raise httpx.ConnectError("down")
    async with httpx.AsyncClient(transport=httpx.MockTransport(down)) as http:
        with pytest.raises(RuntimeError):
            await ResearchService(http, "ua").explore("x y")


def test_read_next_and_timeline_helpers():
    top = [{"related_works": ["https://openalex.org/W3", "https://openalex.org/W4"]},
           {"related_works": ["https://openalex.org/W4"]}]
    assert R.read_next(top, exclude={"W3"}) == ["W4"]
    assert R.timeline([], 2026) == []


# ------------------------------------------------------------------ images
PNG = base64.b64encode(b"\x89PNG\r\n\x1a\nfake").decode()


def test_image_bodies_and_parsing():
    assert build_body("black-forest-labs/flux.1-schnell", "cat", "landscape", 1) | {} == {
        "prompt": "cat", "width": 1344, "height": 768, "steps": 4, "cfg_scale": 0, "seed": 1, "mode": "base"}
    assert build_body("stabilityai/stable-diffusion-3-medium", "cat", "portrait", 1)["aspect_ratio"] == "9:16"
    assert parse_image({"artifacts": [{"base64": "abc", "finishReason": "SUCCESS"}]}) == ("abc", "SUCCESS")
    assert parse_image({"image": "abc", "finish_reason": "SUCCESS"}) == ("abc", "SUCCESS")
    assert parse_image({"data": [{"b64_json": "abc"}]}) == ("abc", "")
    assert parse_image({}) == ("", "")
    assert mime_of(PNG) == "image/png" and mime_of("/9j/4AAQ") == "image/jpeg"


def image_transport(seen, mode="ok"):
    def handler(req: httpx.Request):
        seen.append(req.url.path)
        if req.url.path.endswith("flux.1-schnell"):
            return httpx.Response(404, json={"detail": "Function not found for account"})
        if mode == "filtered":
            return httpx.Response(200, json={"artifacts": [{"base64": "", "finishReason": "CONTENT_FILTERED"}]})
        body = json.loads(req.content)
        assert req.headers["authorization"] == "Bearer nvapi-test" and body["prompt"]
        return httpx.Response(200, json={"artifacts": [{"base64": PNG, "finishReason": "SUCCESS", "seed": 1}]})
    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_image_generator_falls_back_and_skips_dead_models(tmp_path):
    s = make_settings(tmp_path, key="nvapi-test")
    seen = []
    gen = ImageGenerator(s, client=httpx.AsyncClient(transport=image_transport(seen)))
    out = await gen.generate("a robot", "square", seed=3)
    assert out["model"] == "black-forest-labs/flux.1-dev" and out["image"].startswith("data:image/png;base64,")
    assert "black-forest-labs/flux.1-schnell" in gen.dead
    seen.clear()
    await gen.generate("again")
    assert not any(p.endswith("schnell") for p in seen)      # circuit breaker


@pytest.mark.asyncio
async def test_image_generator_errors(tmp_path):
    with pytest.raises(ImageError) as e:
        await ImageGenerator(make_settings(tmp_path)).generate("x")
    assert e.value.status == 503
    s = make_settings(tmp_path, key="nvapi-test")
    gen = ImageGenerator(s, client=httpx.AsyncClient(transport=image_transport([], "filtered")))
    with pytest.raises(ImageError) as e:
        await gen.generate("x")
    assert e.value.status == 400 and "safety" in str(e.value)


def test_api_research_and_image(tmp_path):
    s = make_settings(tmp_path, key="nvapi-test")
    nv = NvidiaClient(s, client=httpx.AsyncClient(transport=nim_transport()))
    app.state.engine = AnswerEngine(s, nv, {"wikipedia": FakeSource("wikipedia", DOCS)})
    app.state.store = ThreadStore(tmp_path / "t.db")
    app.state.research = ResearchService(httpx.AsyncClient(transport=openalex_transport([])), "ua")
    app.state.images = ImageGenerator(s, client=httpx.AsyncClient(transport=image_transport([])))
    with TestClient(app) as c:
        r = c.get("/api/research", params={"q": "rag"}).json()
        assert r["key_papers"][0]["title"].startswith("RAG") and r["timeline"]
        assert c.get("/api/research", params={"q": " "}).status_code == 400

        img = c.post("/api/image", json={"prompt": "a tiger in Mumbai rain", "enhance": False}).json()
        assert img["image"].startswith("data:image/png") and img["prompt"] == "a tiger in Mumbai rain"
        t = c.get(f"/api/threads/{img['thread_id']}").json()
        assert t["focus"] == "image" and t["turns"][0]["meta"]["kind"] == "image"
        assert c.post("/api/image", json={"prompt": "x y", "aspect": "round"}).status_code == 400


def test_api_image_without_key_is_clear(tmp_path):
    s = make_settings(tmp_path)
    app.state.engine = AnswerEngine(s, NvidiaClient(s), {})
    app.state.store = ThreadStore(tmp_path / "t.db")
    app.state.images = ImageGenerator(s)
    with TestClient(app) as c:
        r = c.post("/api/image", json={"prompt": "a cat"})
        assert r.status_code == 503 and "NVIDIA" in r.json()["detail"]


class FakeNV:
    enabled = True

    def __init__(self, reply):
        self.reply = reply

    async def chat(self, messages, **kw):
        assert "image generator" in messages[0]["content"]
        if isinstance(self.reply, Exception):
            raise self.reply
        return self.reply


@pytest.mark.asyncio
async def test_prompt_enhancer_uses_nemotron_and_falls_back(tmp_path):
    gen = ImageGenerator(make_settings(tmp_path, key="nvapi-test"))
    good = "A Bengal tiger prowling a neon-lit Mumbai street in monsoon rain, cinematic night photo"
    assert await gen.enhance(FakeNV('Prompt: "' + good + '"'), "tiger mumbai rain") == good
    assert await gen.enhance(FakeNV('{"questions": ["x"]}'), "tiger") == "tiger"
    assert await gen.enhance(FakeNV(RuntimeError("down")), "tiger") == "tiger"
