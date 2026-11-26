"""Research mode: a literature map for any question, built from OpenAlex (CC0, 250M+ works).

For a topic it returns:
  * key papers      : most relevant works, with citation counts, venue, open-access link
  * foundational    : the most-cited works on the topic
  * rising          : most-cited works from the last ~2 years
  * read next       : works OpenAlex links as related to the top papers, ranked by how often they recur
  * timeline        : how many works were published per year (shows when a field took off)
All calls are cheap JSON requests, so it fits the 512 MB free plan.
"""
from __future__ import annotations

import asyncio
import datetime as dt
import time
from collections import Counter, OrderedDict

import httpx

from .sources.base import clean_text
from .sources.openalex import rebuild_abstract

API = "https://api.openalex.org/works"
SELECT = ("id,doi,title,publication_year,cited_by_count,authorships,primary_location,open_access,"
          "related_works,abstract_inverted_index,type")


def paper(w: dict) -> dict:
    loc = w.get("primary_location") or {}
    oa = w.get("open_access") or {}
    authors = [((a.get("author") or {}).get("display_name") or "") for a in (w.get("authorships") or [])]
    authors = [a for a in authors if a]
    abstract = clean_text(rebuild_abstract(w.get("abstract_inverted_index")))
    return {
        "id": (w.get("id") or "").rsplit("/", 1)[-1],
        "title": clean_text(w.get("title")),
        "year": w.get("publication_year"),
        "cited_by": w.get("cited_by_count") or 0,
        "authors": authors[:3] + (["et al."] if len(authors) > 3 else []),
        "venue": (loc.get("source") or {}).get("display_name"),
        "url": w.get("doi") or loc.get("landing_page_url") or w.get("id"),
        "oa_url": oa.get("oa_url") if oa.get("is_oa") else None,
        "abstract": abstract[:320] + ("…" if len(abstract) > 320 else ""),
    }


def timeline(groups: list[dict], this_year: int, span: int = 30) -> list[dict]:
    rows = []
    for g in groups:
        try:
            y = int(g.get("key"))
        except (TypeError, ValueError):
            continue
        if this_year - span < y <= this_year:
            rows.append({"year": y, "count": int(g.get("count") or 0)})
    rows.sort(key=lambda r: r["year"])
    if rows:   # fill gaps so the chart has one bar per year
        have = {r["year"]: r["count"] for r in rows}
        rows = [{"year": y, "count": have.get(y, 0)} for y in range(rows[0]["year"], rows[-1]["year"] + 1)]
    return rows


def read_next(top: list[dict], exclude: set[str], k: int = 6) -> list[str]:
    """IDs that OpenAlex marks as related to several of the top papers come first."""
    c: Counter = Counter()
    for w in top:
        for rid in (w.get("related_works") or [])[:20]:
            rid = rid.rsplit("/", 1)[-1]
            if rid not in exclude:
                c[rid] += 1
    return [rid for rid, _ in c.most_common(k)]


class ResearchService:
    def __init__(self, http: httpx.AsyncClient, user_agent: str, mailto: str = "", timeout: float = 12.0):
        self.http, self.timeout = http, timeout
        self.headers = {"User-Agent": user_agent}
        self.mailto = mailto
        self._cache: OrderedDict[str, tuple[float, dict]] = OrderedDict()

    async def _get(self, **params) -> dict:
        if self.mailto:
            params["mailto"] = self.mailto
        r = await self.http.get(API, params=params, headers=self.headers, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    async def explore(self, query: str) -> dict:
        key = query.strip().lower()
        hit = self._cache.get(key)
        if hit and time.time() - hit[0] < 3600:
            return hit[1]
        this_year = dt.date.today().year
        calls = {
            "relevant": self._get(search=query, **{"per-page": "8", "select": SELECT}),
            "cited": self._get(search=query, sort="cited_by_count:desc", **{"per-page": "5", "select": SELECT}),
            "rising": self._get(search=query, sort="cited_by_count:desc",
                                filter=f"from_publication_date:{this_year - 2}-01-01",
                                **{"per-page": "5", "select": SELECT}),
            "years": self._get(search=query, group_by="publication_year"),
        }
        out = await asyncio.gather(*calls.values(), return_exceptions=True)
        got = dict(zip(calls, out))
        warnings = [f"openalex:{k}" for k, v in got.items() if isinstance(v, Exception)]
        if len(warnings) == len(calls):
            raise RuntimeError("OpenAlex is unreachable right now")
        res = {k: ([] if isinstance(v, Exception) else v.get("results", [])) for k, v in got.items() if k != "years"}
        total = 0 if isinstance(got["relevant"], Exception) else int((got["relevant"].get("meta") or {}).get("count") or 0)
        years = [] if isinstance(got["years"], Exception) else got["years"].get("group_by", [])

        key_papers = [paper(w) for w in res["relevant"] if w.get("title")]
        seen = {p["id"] for p in key_papers}
        foundational = [p for p in (paper(w) for w in res["cited"] if w.get("title")) if p["id"] not in seen]
        seen |= {p["id"] for p in foundational}
        rising = [p for p in (paper(w) for w in res["rising"] if w.get("title")) if p["id"] not in seen]
        seen |= {p["id"] for p in rising}

        nxt: list[dict] = []
        ids = read_next(res["relevant"][:4], seen)
        if ids:
            try:
                data = await self._get(filter="ids.openalex:" + "|".join(ids), **{"per-page": str(len(ids)), "select": SELECT})
                order = {i: n for n, i in enumerate(ids)}
                nxt = sorted((paper(w) for w in data.get("results", []) if w.get("title")),
                             key=lambda p: order.get(p["id"], 99))
            except Exception:
                warnings.append("openalex:related")

        tl = timeline(years, this_year)
        peak = max(tl, key=lambda r: r["count"]) if tl else None
        result = {
            "query": query, "total_works": total,
            "key_papers": key_papers, "foundational": foundational, "rising": rising, "read_next": nxt,
            "timeline": tl, "peak_year": peak["year"] if peak and peak["count"] else None,
            "warnings": warnings, "source": "OpenAlex (CC0)",
        }
        if not warnings:          # don't pin a partial result for an hour
            self._cache[key] = (time.time(), result)
        while len(self._cache) > 64:
            self._cache.popitem(last=False)
        return result
