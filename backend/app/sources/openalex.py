"""OpenAlex (CC0) — 250M+ scholarly works. Abstracts arrive as an inverted index."""
from __future__ import annotations

from .base import Document, HttpSource, clean_text


def rebuild_abstract(inv: dict | None) -> str:
    if not inv:
        return ""
    pos: list[tuple[int, str]] = []
    for word, idxs in inv.items():
        pos.extend((i, word) for i in idxs)
    return " ".join(w for _, w in sorted(pos))


class OpenAlexSource(HttpSource):
    name = "openalex"
    label = "OpenAlex"

    def __init__(self, *args, mailto: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        self.mailto = mailto

    async def search(self, query: str, limit: int) -> list[Document]:
        params = {"search": query, "per-page": str(limit),
                  "select": "id,doi,title,publication_year,abstract_inverted_index,authorships,primary_location,cited_by_count"}
        if self.mailto:
            params["mailto"] = self.mailto   # OpenAlex "polite pool"
        r = await self.get("https://api.openalex.org/works", **params)
        return parse_openalex(r.json())


def parse_openalex(data: dict) -> list[Document]:
    docs = []
    for w in data.get("results", []):
        title = clean_text(w.get("title"))
        abstract = clean_text(rebuild_abstract(w.get("abstract_inverted_index")))
        if not title:
            continue
        loc = w.get("primary_location") or {}
        url = w.get("doi") or loc.get("landing_page_url") or w.get("id")
        authors = [((a.get("author") or {}).get("display_name") or "") for a in (w.get("authorships") or [])]
        docs.append(Document(
            title=title, url=url, content=f"{title}. {abstract}".strip(), snippet=(abstract or title)[:280],
            source="openalex", published=str(w.get("publication_year") or "") or None,
            authors=[a for a in authors if a][:6],
            extra={"cited_by": w.get("cited_by_count", 0), "venue": ((loc.get("source") or {}).get("display_name")),
                   "license": "CC0 metadata"},
        ))
    return docs
