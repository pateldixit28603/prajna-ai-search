"""Daily "Prajna Daily" digest.

Every day (GitHub Actions cron) this:
  1. pulls what is trending globally in tech from open data (see scripts/tech_trends.py): the Hacker News
     front page, new GitHub repos by stars, Hugging Face daily papers / new arXiv AI papers, and
     Wikipedia most-read filtered to technology, science, companies and products;
  2. sorts the topics into categories (AI & ML, Chips & Hardware, ...) with the NVIDIA NIM LLM,
     falling back to keyword rules;
  3. runs each through the full Prajna pipeline (search -> rank -> NVIDIA rerank -> cited answer);
  4. writes digest/data/<date>.json, DIGEST.md (rendered on GitHub) and a static site in site/
     with category chips (CSS-only filters) and "why it's trending" signals.

Usage:  python -m scripts.daily_digest [--hn 3] [--github 2] [--papers 2] [--wiki 2] [--date YYYY-MM-DD]
"""
from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import html
import json
import os
import re
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from app.config import settings  # noqa: E402
from app.runner import answer, citation_metrics, engine_session  # noqa: E402
from scripts import tech_trends as tt  # noqa: E402

DIGEST = REPO / "digest"
SITE = REPO / "site"


# ------------------------------------------------------------------ topics
async def trending(day: dt.date, counts: dict[str, int]) -> list[dict]:
    """Today's global tech trends (HN, GitHub, papers, tech-only Wikipedia most-read)."""
    return await tt.gather(day, counts, settings.user_agent, os.getenv("GITHUB_TOKEN", ""))


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
nav.archive a{margin-right:10px;font-size:.85rem}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 8px}.chips label{cursor:pointer;border:1px solid var(--line);border-radius:99px;padding:4px 12px;font-size:.85rem;user-select:none}
.chips label:hover{border-color:var(--nv)}.chips b{font-weight:500;opacity:.7;margin-left:2px}.pill.cat{color:var(--nv);border-color:#76b90066}
.sig{font-size:.8rem;color:var(--text);margin-right:4px}.ctx{color:var(--muted);font-size:.9rem;margin:-.3rem 0 .6rem}footer{color:var(--muted);font-size:.8rem;border-top:1px solid var(--line);padding-top:20px;margin-top:20px}
"""


def _cat(it: dict) -> str:
    """Category of an item; older archive items (before categories) get the keyword fallback."""
    c = it.get("category")
    return c if c in tt.CATEGORIES else tt.fallback_category(it)


def category_counts(items: list[dict]) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for it in items:
        counts[_cat(it)] = counts.get(_cat(it), 0) + 1
    return [(k, counts[k]) for k in tt.CATEGORIES if k in counts]


def filter_css(slugs: list[str]) -> str:
    """CSS-only category filter: a hidden radio per category + :has() rules (no JavaScript)."""
    rules = []
    for k in slugs:
        rules.append(f"body:has(#f-{k}:checked) article:not(.c-{k}){{display:none}}")
        rules.append(f"body:has(#f-{k}:checked) label[for=f-{k}]{{background:var(--nv);color:#0b0f0a;border-color:var(--nv)}}")
    rules.append("body:has(#f-all:checked) label[for=f-all]{background:var(--nv);color:#0b0f0a;border-color:var(--nv)}")
    return "\n".join(rules)


def render_page(day: str, items: list[dict], archive: list[str], mode: str) -> str:
    cats = category_counts(items)
    arts = []
    for it in items:
        r, cat = it["result"], _cat(it)
        srcs = "".join(f'<a href="{html.escape(s["url"])}" target="_blank" rel="noopener">{s["n"]} · '
                       f'{html.escape(s["title"])}</a>' for s in r["sources"])
        kind = tt.KIND_LABEL.get(it.get("kind", ""), it.get("kind", ""))
        signal = it.get("signal") or tt.signal_text(it)
        link = (f' · <a href="{html.escape(it["link"])}" target="_blank" rel="noopener">open ↗</a>'
                if it.get("link") else "")
        if it.get("discussion") and it.get("discussion") != it.get("link"):
            link += f' · <a href="{html.escape(it["discussion"])}" target="_blank" rel="noopener">discussion ↗</a>'
        ctx = f'<p class="ctx">{html.escape(it["context"])}</p>' if it.get("context") else ""
        arts.append(f"""<article class="c-{cat}"><div class="meta"><span class="pill cat">{html.escape(tt.LABELS[cat])}</span><span class="pill">{html.escape(kind)}</span><span class="sig">{html.escape(signal)}</span>{link}</div>
<h2>{html.escape(r['question'])}</h2>{ctx}{md_to_html(r['answer'], r['sources'])}<div class="src">{srcs}</div></article>""")
    radios = '<input type="radio" name="cat" id="f-all" checked hidden>' + "".join(
        f'<input type="radio" name="cat" id="f-{k}" hidden>' for k, _ in cats)
    chips = f'<label for="f-all">All <b>{len(items)}</b></label>' + "".join(
        f'<label for="f-{k}">{html.escape(tt.LABELS[k])} <b>{n}</b></label>' for k, n in cats)
    links = " ".join(f'<a href="{d}.html">{d}</a>' for d in archive[:30])
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Prajna Daily — {day}</title><meta name="description" content="What's trending in tech worldwide today, by category, answered with citations by Prajna (NVIDIA NIM + open data).">
<style>{CSS}{filter_css([k for k, _ in cats])}</style></head><body>{radios}<main><header><h1>Prajna <span>Daily</span></h1>
<p class="sub">{day} · what's trending in tech worldwide today, from Hacker News, GitHub, new AI papers and Wikipedia,
grouped by category, then researched and answered with citations by
<a href="https://github.com/pateldixit28603/prajna-ai-search">Prajna</a>, an open-source answer engine on NVIDIA NIM + open data.
<br><span class="pill">mode: {html.escape(mode)}</span></p>
<nav class="chips" aria-label="Filter by category">{chips}</nav></header>
{''.join(arts) or '<p>No topics today.</p>'}
<footer><nav class="archive">Archive: {links}</nav><p>Generated by GitHub Actions. Topics: Hacker News, GitHub, Hugging Face Daily Papers / arXiv, Wikipedia. Answer sources: Wikipedia (CC BY-SA), OpenAlex (CC0), arXiv, Hacker News.</p></footer>
</main></body></html>"""


def render_markdown(day: str, items: list[dict], mode: str) -> str:
    out = [f"# Prajna Daily — {day}", "",
           f"_What's trending in tech worldwide today (Hacker News, GitHub, new AI papers, Wikipedia), grouped by "
           f"category and answered automatically with citations. Mode: **{mode}**. Updated daily by GitHub Actions "
           f"— [archive](digest/data/)._", ""]
    for cat, _ in category_counts(items):
        out += [f"## {tt.LABELS[cat]}", ""]
        for it in (i for i in items if _cat(i) == cat):
            r = it["result"]
            signal = it.get("signal") or tt.signal_text(it)
            out += [f"### {r['question']}", "", f"<sub>{signal}</sub>", "",
                    r["answer"].split("> _Extractive")[0].strip(), "", "<sub>Sources: " +
                    " · ".join(f"[{s['n']}] [{s['title']}]({s['url']})" for s in r["sources"]) + "</sub>", ""]
    return "\n".join(out) + "\n"


# ------------------------------------------------------------------ main
async def main_async(day: dt.date, counts: dict[str, int]) -> None:
    topics = await trending(day, counts)
    print(f"{len(topics)} topics")
    items = []
    async with engine_session() as engine:
        how = await tt.classify(topics, engine.nv, settings.llm_fast_model)
        print(f"categories by: {how}")
        for t in topics:
            try:
                r = await answer(engine, t["question"], t["focus"])
            except Exception as e:
                print("  ! failed:", t["topic"], e)
                continue
            if not r["sources"]:
                continue
            items.append(t | {"result": r, "metrics": citation_metrics(r)})
            print(f"  ✓ [{t['category']}] {t['topic']} ({len(r['sources'])} sources, {r['timings']['total']:.1f}s)")
    order = list(tt.CATEGORIES)
    items.sort(key=lambda it: order.index(_cat(it)))
    n_llm = sum(it["result"]["nvidia"] for it in items)
    mode = f"NVIDIA NIM ({n_llm}/{len(items)} answers by the LLM)" if n_llm else "extractive (no NVIDIA LLM)"
    for it in items:
        it["result"].pop("passages", None)

    ds = day.isoformat()
    (DIGEST / "data").mkdir(parents=True, exist_ok=True)
    (DIGEST / "data" / f"{ds}.json").write_text(
        json.dumps({"date": ds, "mode": mode, "categories_by": how, "items": items}, indent=2, ensure_ascii=False),
        encoding="utf-8")
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
    ap.add_argument("--hn", type=int, default=3, help="Hacker News front-page stories")
    ap.add_argument("--github", type=int, default=2, help="new GitHub repos by stars")
    ap.add_argument("--papers", type=int, default=2, help="Hugging Face daily papers (arXiv fallback)")
    ap.add_argument("--wiki", type=int, default=2, help="tech-only Wikipedia most-read articles")
    ap.add_argument("--date", type=dt.date.fromisoformat, default=dt.datetime.now(dt.timezone.utc).date())
    a = ap.parse_args()
    asyncio.run(main_async(a.date, {"hn": a.hn, "github": a.github, "papers": a.papers, "wiki": a.wiki}))


if __name__ == "__main__":
    main()
