"""arXiv open-access preprints via the public Atom API."""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET

from .base import Document, HttpSource, clean_text

NS = {"a": "http://www.w3.org/2005/Atom"}
_WORD = re.compile(r"[\w-]+", re.UNICODE)


class ArxivSource(HttpSource):
    name = "arxiv"
    label = "arXiv"

    async def search(self, query: str, limit: int) -> list[Document]:
        terms = [w for w in _WORD.findall(query) if len(w) > 2][:8]
        if not terms:
            return []
        q = " AND ".join(f"all:{t}" for t in terms)
        r = await self.get("https://export.arxiv.org/api/query",
                           search_query=q, start="0", max_results=str(limit), sortBy="relevance")
        return parse_arxiv(r.text)


def parse_arxiv(xml_text: str) -> list[Document]:
    root = ET.fromstring(xml_text)
    docs = []
    for e in root.findall("a:entry", NS):
        title = clean_text(e.findtext("a:title", default="", namespaces=NS))
        summary = clean_text(e.findtext("a:summary", default="", namespaces=NS))
        url = (e.findtext("a:id", default="", namespaces=NS) or "").replace("http://", "https://")
        if not title or not url:
            continue
        authors = [clean_text(a.findtext("a:name", default="", namespaces=NS)) for a in e.findall("a:author", NS)]
        docs.append(Document(
            title=title, url=url, content=f"{title}. {summary}", snippet=summary[:280],
            source="arxiv", published=(e.findtext("a:published", default="", namespaces=NS) or "")[:10] or None,
            authors=[a for a in authors if a][:6], extra={"license": "arXiv"},
        ))
    return docs
