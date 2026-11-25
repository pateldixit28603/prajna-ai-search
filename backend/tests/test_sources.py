import httpx
import pytest

from app.sources.arxiv import parse_arxiv
from app.sources.hackernews import parse_hn
from app.sources.openalex import parse_openalex, rebuild_abstract
from app.sources.wikipedia import WikipediaSource

ARXIV = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/1706.03762v7</id>
    <published>2017-06-12T17:57:34Z</published>
    <title>Attention Is All You
      Need</title>
    <summary>The dominant sequence transduction models are based on recurrent networks.</summary>
    <author><name>Ashish Vaswani</name></author>
  </entry>
</feed>"""


def test_parse_arxiv():
    d = parse_arxiv(ARXIV)[0]
    assert d.title == "Attention Is All You Need"
    assert d.url.startswith("https://arxiv.org/abs/1706.03762")
    assert d.published == "2017-06-12" and d.authors == ["Ashish Vaswani"]


def test_openalex_abstract_rebuild_and_parse():
    assert rebuild_abstract({"GPUs": [0], "are": [1], "fast": [2]}) == "GPUs are fast"
    docs = parse_openalex({"results": [{
        "id": "https://openalex.org/W1", "doi": "https://doi.org/10.1/x", "title": "Deep GPUs",
        "publication_year": 2020, "abstract_inverted_index": {"Hello": [0], "world": [1]},
        "authorships": [{"author": {"display_name": "A. Turing"}}], "cited_by_count": 5}]})
    assert docs[0].url == "https://doi.org/10.1/x" and "Hello world" in docs[0].content
    assert docs[0].extra["cited_by"] == 5


def test_parse_hn():
    docs = parse_hn({"hits": [{"objectID": "1", "title": "Show HN: GPU thing", "url": None,
                               "author": "pg", "points": 10, "num_comments": 3, "story_text": "<p>Body &amp; text</p>"}]})
    assert docs[0].url == "https://news.ycombinator.com/item?id=1"
    assert "Body & text" in docs[0].content


@pytest.mark.asyncio
async def test_wikipedia_uses_hindi_edition_for_devanagari():
    seen = []

    def handler(req):
        seen.append(req.url.host)
        return httpx.Response(200, json={"query": {"pages": [{
            "title": "एनवीडिया", "index": 1, "fullurl": "https://hi.wikipedia.org/wiki/x",
            "extract": "एनवीडिया एक अमेरिकी प्रौद्योगिकी कंपनी है " * 5}]}})

    src = WikipediaSource(httpx.AsyncClient(transport=httpx.MockTransport(handler)), "ua")
    docs = await src.search("एनवीडिया क्या है", 3)
    assert seen[0] == "hi.wikipedia.org" and docs
