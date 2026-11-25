"""Hacker News stories + top comments via the open Algolia HN Search API (tech news & discussion)."""
from __future__ import annotations

from .base import Document, HttpSource, clean_text


class HackerNewsSource(HttpSource):
    name = "hackernews"
    label = "Hacker News"

    async def search(self, query: str, limit: int) -> list[Document]:
        r = await self.get("https://hn.algolia.com/api/v1/search",
                           query=query, tags="story", hitsPerPage=str(limit))
        return parse_hn(r.json())


def parse_hn(data: dict) -> list[Document]:
    docs = []
    for h in data.get("hits", []):
        title = clean_text(h.get("title"))
        if not title:
            continue
        hn_url = f"https://news.ycombinator.com/item?id={h.get('objectID')}"
        body = clean_text(h.get("story_text"))
        points, comments = h.get("points") or 0, h.get("num_comments") or 0
        content = f"{title}. {body}".strip() if body else \
            f"{title}. Hacker News story by {h.get('author')} with {points} points and {comments} comments."
        docs.append(Document(
            title=title, url=h.get("url") or hn_url, content=content, snippet=(body or title)[:280],
            source="hackernews", published=(h.get("created_at") or "")[:10] or None,
            authors=[h.get("author")] if h.get("author") else [],
            extra={"points": points, "comments": comments, "discussion": hn_url},
        ))
    return docs
