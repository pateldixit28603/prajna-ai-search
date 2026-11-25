"""Daily "Prajna Daily" digest.

Every day (GitHub Actions cron) this:
  1. pulls today's trending topics from open data — Wikipedia "most read" (Wikimedia feed API)
     and the Hacker News front page (Algolia API);
  2. runs each through the full Prajna pipeline (search -> rank -> NVIDIA rerank -> cited answer);
  3. writes digest/data/<date>.json, DIGEST.md (rendered on GitHub) and a static site in site/.

Usage:  python -m scripts.daily_digest [--wiki 4] [--hn 3] [--date YYYY-MM-DD]
"""
from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import html
import json
import re
import sys
from pathlib import Path

import httpx

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from app.config import settings  # noqa: E402
from app.runner import answer, citation_metrics, engine_session  # noqa: E402

DIGEST = REPO / "digest"
SITE = REPO / "site"
SKIP = re.compile(r"^(Main_Page|Special:|Wikipedia:|Portal:|File:|Deaths_in|List_of|\d{4}_in)", re.I)


# ------------------------------------------------------------------ topics
async def trending(day: dt.date, n_wiki: int, n_hn: int) -> list[dict]:
    topics: list[dict] = []
    headers = {"User-Agent": settings.user_agent}
    async with httpx.AsyncClient(timeout=20, headers=headers, follow_redirects=True) as c:
        # Wikipedia most-read is published for the previous day
        ref = day - dt.timedelta(days=1)
        try:
            r = await c.get(f"https://en.wikipedia.org/api/rest_v1/feed/featured/{ref:%Y/%m/%d}")
            arts = (r.json().get("mostread") or {}).get("articles", [])
            for a in arts:
                if SKIP.search(a.get("title", "")) or a.get("type", "standard") != "standard":
                    continue
                name = a.get("normalizedtitle") or a["title"].replace("_", " ")
                topics.append({
                    "kind": "wikipedia", "topic": name, "views": a.get("views"),
                    "question": f"Who or what is {name}, and what are the key facts to know?",
                    "focus": "wiki", "context": a.get("description", ""),
                })
                if len(topics) >= n_wiki:
                    break
        except Exception as e:
            print("wikipedia trending failed:", e)
        try:
            r = await c.get("https://hn.algolia.com/api/v1/search", params={"tags": "front_page", "hitsPerPage": 30})
            hits = sorted(r.json().get("hits", []), key=lambda h: -(h.get("points") or 0))
            added = 0
            for h in hits:
                t = h.get("title") or ""
                if not t or t.lower().startswith(("ask hn", "show hn", "tell hn")):
                    continue
                clean = re.sub(r"\s*\[[^\]]*\]|\s*\(\d{4}\)", "", t).strip()
                topics.append({
                    "kind": "hackernews", "topic": clean, "points": h.get("points"),
                    "discussion": f"https://news.ycombinator.com/item?id={h.get('objectID')}",
                    "question": f"{clean} — what is this about and why does it matter?", "focus": "all",
                })
                added += 1
                if added >= n_hn:
                    break
        except Exception as e:
            print("hacker news trending failed:", e)
    return topics


# ------------------------------------------------------------- rendering
def md_to_html(md: str, sources: list[dict]) -> str:
    """Tiny, safe Markdown subset: paragraphs, bullet lists, bold, [n] citations."""
    by_n = {str(s["n"]): s for s in sources}

    def inline(t: str) -> str:
        t = html.escape(t)
        t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
        t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)

        def cite(m):
            s = by_n.get(m.group(1))
            if not s:
                return m.group(0)
            return (f'<a class="cite" href="{html.escape(s["url"])}" title="{html.escape(s["title"])}" '
                    f'target="_blank" rel="noopener">{m.group(1)}</a>')
        return re.sub(r"\[(\d{1,2})\]", cite, t)

    out, in_list = [], False
    for line in md.split("\n"):
        s = line.strip()
        if s.startswith(("- ", "* ")):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{inline(s[2:])}</li>")
            continue
        if in_list:
            out.append("</ul>")
            in_list = False
        if not s or s.startswith("> _Extractive"):
            continue
        if s.startswith("#"):
            out.append(f"<h4>{inline(s.lstrip('# '))}</h4>")
        else:
            out.append(f"<p>{inline(s)}</p>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


CSS = """
:root{--ink:#0b0f0a;--panel:#121812;--line:#263026;--muted:#8a978a;--text:#e7ede4;--nv:#76b900}
*{box-sizing:border-box}body{margin:0;background:var(--ink);color:var(--text);font:16px/1.7 Inter,system-ui,sans-serif}
a{color:var(--nv)}main{max-width:820px;margin:0 auto;padding:48px 20px 80px}
header h1{font:600 2.6rem/1.1 Fraunces,Georgia,serif;margin:0}header h1 span{color:var(--nv)}
.sub{color:var(--muted);margin:.6rem 0 2rem}.pill{display:inline-block;border:1px solid var(--line);border-radius:99px;padding:2px 10px;font-size:.78rem;color:var(--muted);margin-right:6px}
article{border-top:1px solid var(--line);padding:28px 0}article h2{font:600 1.45rem/1.3 Fraunces,Georgia,serif;margin:.4rem 0 .8rem}
.meta{font-size:.8rem;color:var(--muted)}.cite{display:inline-block;min-width:1.2em;padding:0 .35em;margin:0 1px;border-radius:99px;background:#76b90022;color:var(--nv);font:500 .7rem/1.5 ui-monospace,monospace;text-decoration:none;vertical-align:.15em}
.src{display:flex;flex-wrap:wrap;gap:6px;margin:12px 0 0}.src a{font-size:.78rem;border:1px solid var(--line);border-radius:8px;padding:4px 8px;color:var(--text);text-decoration:none;max-width:250px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.src a:hover{border-color:var(--nv)}li::marker{color:var(--nv)}code{background:var(--panel);padding:0 4px;border-radius:4px}
nav.archive a{margin-right:10px;font-size:.85rem}footer{color:var(--muted);font-size:.8rem;border-top:1px solid var(--line);padding-top:20px;margin-top:20px}
"""


def render_page(day: str, items: list[dict], archive: list[str], mode: str) -> str:
    arts = []
    for it in items:
        r = it["result"]
        srcs = "".join(f'<a href="{html.escape(s["url"])}" target="_blank" rel="noopener">{s["n"]} · '
                       f'{html.escape(s["title"])}</a>' for s in r["sources"])
        badge = "Wikipedia most-read" if it["kind"] == "wikipedia" else "Hacker News front page"
        arts.append(f"""<article><div class="meta"><span class="pill">{badge}</span>{html.escape(it.get('context') or '')}</div>
<h2>{html.escape(r['question'])}</h2>{md_to_html(r['answer'], r['sources'])}<div class="src">{srcs}</div></article>""")
    links = " ".join(f'<a href="{d}.html">{d}</a>' for d in archive[:30])
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Prajna Daily — {day}</title><meta name="description" content="What the internet is curious about today, answered with citations by Prajna (NVIDIA NIM + open data).">
<style>{CSS}</style></head><body><main><header><h1>Prajna <span>Daily</span></h1>
<p class="sub">{day} · today's trending topics from Wikipedia and Hacker News, researched and answered automatically by
<a href="https://github.com/pateldixit28603/prajna-ai-search">Prajna</a> — an open-source answer engine on NVIDIA NIM + open data.
<br><span class="pill">mode: {html.escape(mode)}</span></p></header>
{''.join(arts) or '<p>No topics today.</p>'}
<footer><nav class="archive">Archive: {links}</nav><p>Generated by GitHub Actions. Sources: Wikipedia (CC BY-SA), OpenAlex (CC0), arXiv, Hacker News.</p></footer>
</main></body></html>"""


def render_markdown(day: str, items: list[dict], mode: str) -> str:
    out = [f"# Prajna Daily — {day}", "",
           f"_Today's trending topics (Wikipedia most-read + Hacker News front page), answered automatically with "
           f"citations. Mode: **{mode}**. Updated daily by GitHub Actions — [archive](digest/data/)._", ""]
    for it in items:
        r = it["result"]
        out += [f"## {r['question']}", "", r["answer"].split("> _Extractive")[0].strip(), "", "<sub>Sources: " +
                " · ".join(f"[{s['n']}] [{s['title']}]({s['url']})" for s in r["sources"]) + "</sub>", ""]
    return "\n".join(out) + "\n"


# ------------------------------------------------------------------ main
async def main_async(day: dt.date, n_wiki: int, n_hn: int) -> None:
    topics = await trending(day, n_wiki, n_hn)
    print(f"{len(topics)} topics")
    items = []
    async with engine_session() as engine:
        for t in topics:
            try:
                r = await answer(engine, t["question"], t["focus"])
            except Exception as e:
                print("  ! failed:", t["topic"], e)
                continue
            if not r["sources"]:
                continue
            items.append(t | {"result": r, "metrics": citation_metrics(r)})
            print(f"  ✓ {t['topic']} ({len(r['sources'])} sources, {r['timings']['total']:.1f}s)")
    n_llm = sum(it["result"]["nvidia"] for it in items)
    mode = f"NVIDIA NIM ({n_llm}/{len(items)} answers by the LLM)" if n_llm else "extractive (no NVIDIA LLM)"
    for it in items:
        it["result"].pop("passages", None)

    ds = day.isoformat()
    (DIGEST / "data").mkdir(parents=True, exist_ok=True)
    (DIGEST / "data" / f"{ds}.json").write_text(
        json.dumps({"date": ds, "mode": mode, "items": items}, indent=2, ensure_ascii=False), encoding="utf-8")
    archive = sorted((p.stem for p in (DIGEST / "data").glob("*.json")), reverse=True)
    (DIGEST / "index.json").write_text(json.dumps(archive), encoding="utf-8")
    (REPO / "DIGEST.md").write_text(render_markdown(ds, items, mode), encoding="utf-8")

    SITE.mkdir(exist_ok=True)
    for d in archive[:60]:   # (re)render recent pages so archive links stay current
        data = json.loads((DIGEST / "data" / f"{d}.json").read_text(encoding="utf-8"))
        (SITE / f"{d}.html").write_text(render_page(d, data["items"], archive, data["mode"]), encoding="utf-8")
    (SITE / "index.html").write_text(render_page(ds, items, archive, mode), encoding="utf-8")
    (SITE / ".nojekyll").write_text("")
    print(f"wrote DIGEST.md, site/ ({len(items)} answers, mode={mode})")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wiki", type=int, default=4)
    ap.add_argument("--hn", type=int, default=3)
    ap.add_argument("--date", type=dt.date.fromisoformat, default=dt.datetime.now(dt.timezone.utc).date())
    a = ap.parse_args()
    asyncio.run(main_async(a.date, a.wiki, a.hn))


if __name__ == "__main__":
    main()
