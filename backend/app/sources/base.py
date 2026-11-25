from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field, asdict
from typing import Protocol

import httpx


@dataclass
class Document:
    title: str
    url: str
    content: str
    source: str                      # "wikipedia", "arxiv", "openalex", "hackernews", "local"
    snippet: str = ""
    published: str | None = None
    authors: list[str] = field(default_factory=list)
    extra: dict = field(default_factory=dict)

    @property
    def id(self) -> str:
        return hashlib.sha1(self.url.encode()).hexdigest()[:12]

    def to_public(self) -> dict:
        d = asdict(self)
        d["id"] = self.id
        d.pop("content", None)
        d["snippet"] = self.snippet or self.content[:280]
        d["domain"] = domain_of(self.url)
        return d


class SearchSource(Protocol):
    name: str
    label: str

    async def search(self, query: str, limit: int) -> list[Document]: ...


_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


def clean_text(text: str | None) -> str:
    if not text:
        return ""
    text = _TAG.sub(" ", text)
    text = (text.replace("&quot;", '"').replace("&#x27;", "'").replace("&#39;", "'")
                .replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&#x2F;", "/"))
    return _WS.sub(" ", text).strip()


def domain_of(url: str) -> str:
    if (url or "").startswith("file:"):
        return "local file"
    m = re.match(r"https?://([^/]+)", url or "")
    return (m.group(1) if m else "").removeprefix("www.")


class HttpSource:
    """Base class giving every source a shared, polite HTTP client."""

    name = "base"
    label = "Base"

    def __init__(self, client: httpx.AsyncClient, user_agent: str, timeout: float = 12.0):
        self.client = client
        self.headers = {"User-Agent": user_agent}
        self.timeout = timeout

    async def get(self, url: str, **params) -> httpx.Response:
        r = await self.client.get(url, params=params, headers=self.headers, timeout=self.timeout)
        r.raise_for_status()
        return r
