"""Wikipedia (CC BY-SA) via the public MediaWiki Action API. Supports any language edition."""
from __future__ import annotations

import re

from .base import Document, HttpSource, clean_text

_DEVANAGARI = re.compile(r"[ऀ-ॿ]")


class WikipediaSource(HttpSource):
    name = "wikipedia"
    label = "Wikipedia"

    def __init__(self, *args, lang: str = "en", **kwargs):
        super().__init__(*args, **kwargs)
        self.lang = lang

    async def search(self, query: str, limit: int) -> list[Document]:
        langs = [self.lang]
        if _DEVANAGARI.search(query) and "hi" not in langs:
            langs.insert(0, "hi")          # Hindi query -> search Hindi Wikipedia first
        docs: list[Document] = []
        for lang in langs:
            docs.extend(await self._search_lang(query, limit, lang))
        return docs[:limit]

    async def _search_lang(self, query: str, limit: int, lang: str) -> list[Document]:
        api = f"https://{lang}.wikipedia.org/w/api.php"
        r = await self.get(
            api,
            action="query", format="json", formatversion="2",
            generator="search", gsrsearch=query, gsrlimit=str(limit), gsrprop="snippet",
            prop="extracts|info|pageprops", exintro="0", explaintext="1", exlimit="max",
            exchars="6000", inprop="url",
        )
        pages = r.json().get("query", {}).get("pages", [])
        pages.sort(key=lambda p: p.get("index", 999))
        docs = []
        for p in pages:
            if "disambiguation" in (p.get("pageprops") or {}):
                continue
            text = clean_text(p.get("extract"))
            if len(text) < 80:
                continue
            docs.append(Document(
                title=p["title"],
                url=p.get("fullurl") or f"https://{lang}.wikipedia.org/wiki/{p['title'].replace(' ', '_')}",
                content=text,
                snippet=text[:280],
                source=self.name,
                extra={"lang": lang, "license": "CC BY-SA 4.0"},
            ))
        return docs
