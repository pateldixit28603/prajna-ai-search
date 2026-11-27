"""Global tech-trends digest: sources, categories (NVIDIA + keyword fallback), rendering."""
import datetime as dt

import httpx

from scripts import daily_digest as dd
from scripts import tech_trends as tt


def test_keyword_categories():
    assert tt.keyword_category("NVIDIA unveils Rubin GPU") == "chips"
    assert tt.keyword_category("A new open-weight LLM beats GPT-5") == "ai"
    assert tt.keyword_category("Critical zero-day in OpenSSH") == "security"
    assert tt.keyword_category("SpaceX Starship reaches orbit") == "science"
    assert tt.keyword_category("iPhone 18 review") == "gadgets"
    assert tt.keyword_category("Writing a compiler in Rust") == "software"
    assert tt.keyword_category("Thanksgiving") is None


def test_wikipedia_tech_filter():
    assert tt.is_tech("Nvidia", "American technology company")
    assert tt.is_tech("ChatGPT", "Chatbot developed by OpenAI")
    assert not tt.is_tech("Thanksgiving", "Holiday in the United States and Canada")
    assert not tt.is_tech("Taylor Swift", "American singer-songwriter (born 1989)")


def test_fallback_uses_kind_default():
    assert tt.fallback_category({"kind": "github", "topic": "foo/bar", "context": "A tiny thing"}) == "opensource"
    assert tt.fallback_category({"kind": "paper", "topic": "On widgets"}) == "ai"


def test_parse_categories_is_strict():
    assert tt.parse_categories('Sure! {"1": "ai", "2": "CHIPS", "3": "sports", "9": "ai"}', 3) == {1: "ai", 2: "chips"}
    assert tt.parse_categories("no json here", 2) == {}
    assert tt.parse_categories("{broken", 2) == {}


class FakeNV:
    enabled = True

    def __init__(self, reply=None, error=None):
        self.reply, self.error, self.calls = reply, error, []

    async def chat(self, messages, **kw):
        self.calls.append(messages)
        if self.error:
            raise self.error
        return self.reply


TOPICS = [{"kind": "hackernews", "topic": "Show HN: my terminal emulator", "points": 512, "comments": 80},
          {"kind": "github", "topic": "acme/agent", "context": "AI agents framework", "stars": 900}]


async def test_classify_with_nvidia():
    topics = [dict(t) for t in TOPICS]
    nv = FakeNV('{"1": "software", "2": "ai"}')
    assert await tt.classify(topics, nv) == "nvidia"
    assert [t["category"] for t in topics] == ["software", "ai"]
    assert all(t["category_by"] == "nvidia" for t in topics)
    assert topics[0]["signal"] == "▲ 512 points on Hacker News · 80 comments"
    assert "acme/agent" in nv.calls[0][1]["content"]


async def test_classify_falls_back_when_nvidia_fails():
    topics = [dict(t) for t in TOPICS]
    assert await tt.classify(topics, FakeNV(error=RuntimeError("timeout"))) == "keywords"
    assert [t["category"] for t in topics] == ["software", "ai"]
    topics = [dict(t) for t in TOPICS]
    assert await tt.classify(topics, FakeNV('{"2": "opensource"}')) == "mixed"
    assert topics[1]["category"] == "opensource" and topics[0]["category_by"] == "keywords"


def _client(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


async def test_fetchers_parse_open_apis():
    def handler(req: httpx.Request):
        h = req.url.host
        if h == "hn.algolia.com":
            return httpx.Response(200, json={"hits": [
                {"title": "Ask HN: anything?", "points": 999, "objectID": "1"},
                {"title": "Show HN: Tiny GPU [video]", "points": 300, "num_comments": 12, "objectID": "2",
                 "url": "https://example.com/gpu"}]})
        if h == "api.github.com":
            assert "created:>=2026-11-19" in req.url.params["q"] and req.url.params["sort"] == "stars"
            return httpx.Response(200, json={"items": [
                {"full_name": "a/nodesc", "description": None, "stargazers_count": 10},
                {"full_name": "b/fast-llm", "description": "Fast LLM inference", "stargazers_count": 5000,
                 "language": "Rust", "created_at": "2026-11-21T00:00:00Z", "html_url": "https://github.com/b/fast-llm"}]})
        if h == "huggingface.co":
            return httpx.Response(200, json=[{"paper": {"id": "2611.00001", "title": "Small Models", "upvotes": 3}},
                                             {"paper": {"id": "2611.00002", "title": "Big  Ideas", "upvotes": 40}}])
        if h == "en.wikipedia.org":
            assert "/2026/11/25" in req.url.path
            return httpx.Response(200, json={"mostread": {"articles": [
                {"title": "Thanksgiving", "description": "Holiday", "views": 900000},
                {"title": "OpenAI", "normalizedtitle": "OpenAI", "description": "American AI company", "views": 50000}]}})
        return httpx.Response(404)

    async with _client(handler) as c:
        hn = await tt.hn_topics(c, 3)
        gh = await tt.github_topics(c, dt.date(2026, 11, 26), 3)
        papers = await tt.paper_topics(c, 1)
        wiki = await tt.wiki_tech_topics(c, dt.date(2026, 11, 26), 3)
    assert [t["topic"] for t in hn] == ["Tiny GPU"] and hn[0]["link"] == "https://example.com/gpu"
    assert [t["topic"] for t in gh] == ["b/fast-llm"] and gh[0]["stars"] == 5000
    assert papers[0]["topic"] == "Big Ideas" and papers[0]["link"].endswith("2611.00002")
    assert [t["topic"] for t in wiki] == ["OpenAI"] and wiki[0]["views"] == 50000


async def test_papers_fall_back_to_arxiv():
    atom = ('<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>http://arxiv.org/abs/2611.1</id>'
            '<title>New Paper</title><summary>We do things.</summary></entry></feed>')

    def handler(req):
        if req.url.host == "huggingface.co":
            return httpx.Response(503)
        return httpx.Response(200, text=atom)

    async with _client(handler) as c:
        papers = await tt.paper_topics(c, 2)
    assert papers[0]["topic"] == "New Paper" and "upvotes" not in papers[0]
    assert tt.signal_text(papers[0]) == "New on arXiv"


def test_old_archive_items_still_render():
    old = {"kind": "hackernews", "topic": "Rust 2.0", "points": 10,
           "result": {"question": "Rust 2.0?", "answer": "Rust is a language [1].",
                      "sources": [{"n": 1, "title": "Rust", "url": "https://en.wikipedia.org/wiki/Rust"}]}}
    page = dd.render_page("2026-11-25", [old], ["2026-11-25"], "extractive")
    assert 'article class="c-software"' in page and "▲ 10 points on Hacker News" in page
    assert "#f-software:checked" in page and "<script" not in page
