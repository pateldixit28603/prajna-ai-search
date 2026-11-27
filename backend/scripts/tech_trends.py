"""Global tech-trend topics for Prajna Daily, grouped into categories.

Open sources (no keys needed, no RSS):
  * Hacker News front page (Algolia API)          -> signal: points + comments
  * GitHub: new repos sorted by stars (search API) -> signal: stars
  * Hugging Face daily papers (falls back to new arXiv cs.AI/CL/LG/CV) -> signal: upvotes
  * Wikipedia most-read, kept only when it is about tech/science/companies/products -> signal: views

Categories are assigned by the NVIDIA NIM LLM (one batched call to the fast model) and fall back to
keyword rules when NVIDIA is unavailable or answers with something unusable.
"""
from __future__ import annotations

import datetime as dt
import json
import re

import httpx

# slug -> (label, keyword rule). Order matters for the keyword fallback: first match wins.
CATEGORIES: dict[str, tuple[str, str]] = {
    "security": ("Security", r"secur|vulnerab|exploit|malware|ransomware|breach|hack(ed|ers?)\b|cve-|phishing|"
                 r"zero[- ]day|encrypt|privacy|backdoor|botnet|spyware|password|surveillance"),
    "chips": ("Chips & Hardware", r"nvidia|\bgpus?\b|\bcpus?\b|\bchips?\b|semiconductor|tsmc|\bintel\b|\bamd\b|"
              r"arm holdings|risc-v|silicon|wafer|\bnpu\b|\btpu\b|cuda|blackwell|rubin|transistor|datacent|data cent|"
              r"supercomput|fpga|rdna|hbm|\bdram\b|processor"),
    "ai": ("AI & ML", r"\bai\b|artificial intelligence|machine learning|\bllms?\b|language model|neural|"
           r"deep learning|transformer|diffusion|\bgpt|chatgpt|claude (ai|code)|google gemini|gemini (ai|model)|llama \d|openai|anthropic|deepmind|"
           r"ai agents?|agentic|reinforcement learning|\brag\b|embedding|fine-tun|inference|multimodal|"
           r"chatbot|vision-language|reasoning model|\bml\b|hugging ?face|nemotron|mistral|qwen|deepseek"),
    "science": ("Science & Space", r"\bspace\b|spacecraft|nasa|\besa\b|isro|rocket|satellite|orbit|astronom|galaxies|milky way|"
                r"telescope|planet|\bmoon\b|\bmars\b|asteroid|comet|physic|quantum|fusion|particle|"
                r"genom|\bdna\b|biolog|chemis|climate|scientist|neuroscien|crispr|vaccine|starship"),
    "gadgets": ("Gadgets", r"iphone|smartphone|\bphone\b|android|google pixel|pixel \d|galaxy s\d|laptop|macbook|\bipad\b|tablet|"
                r"headset|vision pro|wearable|smartwatch|earbuds|camera|console|playstation|xbox|nintendo|"
                r"switch 2|steam deck|video game|gaming|\bgta\b|\bev\b|electric vehicle|drone|gadget|keyboard"),
    "bigtech": ("Big Tech & Startups", r"google|alphabet|apple|microsoft|\bmeta\b|facebook|amazon|\baws\b|"
                r"tesla|spacex|netflix|samsung|tiktok|bytedance|alibaba|tencent|baidu|x\.com|twitter|"
                r"technology company|tech company|startup|funding|acquisition|acquires|valuation|\bipo\b|"
                r"antitrust|technology entrepreneur|tech entrepreneur|silicon valley|layoffs|y combinator"),
    "opensource": ("Open Source", r"open[- ]source|\bgithub\b|\blicen[cs]e\b|\bgpl\b|\bmit license|linux|"
                   r"\bfoss\b|self-host|fork(ed)?\b|maintainer|apache"),
    "software": ("Software & Dev Tools", r"programming|software|\bcode\b|compiler|\brust\b|python|javascript|"
                 r"typescript|golang|database|postgres|sqlite|\bapi\b|framework|library|kernel|"
                 r"browser|developer|devtools|\bide\b|terminal|emulat|web\b|cloud|kubernetes|docker|"
                 r"operating system|\bos\b|algorithm|computer|app\b"),
}
LABELS = {k: v[0] for k, v in CATEGORIES.items()}
_RULES = [(k, re.compile(v[1], re.I)) for k, v in CATEGORIES.items()]
KIND_DEFAULT = {"github": "opensource", "paper": "ai", "hackernews": "software", "wikipedia": "bigtech"}
KIND_LABEL = {"hackernews": "Hacker News", "github": "GitHub", "paper": "Papers", "wikipedia": "Wikipedia"}

SKIP_WIKI = re.compile(r"^(Main_Page|Special:|Wikipedia:|Portal:|File:|Deaths_in|List_of|\d{4}_in)", re.I)


def keyword_category(text: str) -> str | None:
    for slug, rx in _RULES:
        if rx.search(text or ""):
            return slug
    return None


def fallback_category(topic: dict) -> str:
    text = " ".join(str(topic.get(k) or "") for k in ("topic", "context", "language"))
    return keyword_category(text) or KIND_DEFAULT.get(topic.get("kind", ""), "software")


def is_tech(title: str, description: str) -> bool:
    """Wikipedia most-read filter: keep only articles about tech, science, companies or products."""
    return keyword_category(f"{title} {description}") is not None


def signal_text(t: dict) -> str:
    """Human-readable 'why it's trending' line."""
    k = t.get("kind")
    if k == "hackernews":
        s = f"▲ {t.get('points') or 0:,} points on Hacker News"
        return s + (f" · {t['comments']:,} comments" if t.get("comments") else "")
    if k == "github":
        s = f"★ {t.get('stars') or 0:,} GitHub stars" + (f" since {t['created']}" if t.get("created") else "")
        return s + (f" · {t['language']}" if t.get("language") else "")
    if k == "paper":
        if t.get("upvotes") is not None:
            return f"▲ {t['upvotes']:,} upvotes on Hugging Face Daily Papers"
        return "New on arXiv"
    if k == "wikipedia":
        return f"👁 {t.get('views') or 0:,} Wikipedia views yesterday"
    return ""


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


# ------------------------------------------------------------------ fetchers
async def hn_topics(c: httpx.AsyncClient, n: int) -> list[dict]:
    r = await c.get("https://hn.algolia.com/api/v1/search", params={"tags": "front_page", "hitsPerPage": 40})
    r.raise_for_status()
    out = []
    for h in sorted(r.json().get("hits", []), key=lambda h: -(h.get("points") or 0)):
        t = h.get("title") or ""
        if not t or t.lower().startswith(("ask hn", "tell hn")):
            continue
        clean = re.sub(r"\s*\[[^\]]*\]|\s*\(\d{4}\)|^show hn:\s*", "", t, flags=re.I).strip()
        out.append({
            "kind": "hackernews", "topic": clean, "points": h.get("points"), "comments": h.get("num_comments"),
            "link": h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
            "discussion": f"https://news.ycombinator.com/item?id={h.get('objectID')}",
            "question": f"{clean} — what is this about and why does it matter?", "focus": "all",
        })
        if len(out) >= n:
            break
    return out


async def github_topics(c: httpx.AsyncClient, day: dt.date, n: int, token: str = "") -> list[dict]:
    since = day - dt.timedelta(days=7)
    headers = {"Accept": "application/vnd.github+json"} | ({"Authorization": f"Bearer {token}"} if token else {})
    r = await c.get("https://api.github.com/search/repositories", headers=headers,
                    params={"q": f"created:>={since.isoformat()}", "sort": "stars", "order": "desc", "per_page": 20})
    r.raise_for_status()
    out = []
    for repo in r.json().get("items", []):
        desc = (repo.get("description") or "").strip()
        if not desc or repo.get("fork") or repo.get("archived"):
            continue
        name = repo["full_name"]
        out.append({
            "kind": "github", "topic": name, "context": desc, "stars": repo.get("stargazers_count"),
            "language": repo.get("language") or "", "created": (repo.get("created_at") or "")[:10],
            "link": repo.get("html_url"),
            "question": f"What is the new open-source project {name.split('/')[-1]} ({desc[:160]}), "
                        f"and why is it getting attention?",
            "focus": "all",
        })
        if len(out) >= n:
            break
    return out


async def paper_topics(c: httpx.AsyncClient, n: int) -> list[dict]:
    out: list[dict] = []
    try:
        r = await c.get("https://huggingface.co/api/daily_papers", params={"limit": 30})
        rows = r.json() if r.status_code < 400 else []
        papers = []
        for row in rows if isinstance(rows, list) else []:
            p = row.get("paper") or row
            if p.get("title") and p.get("id"):
                papers.append(p)
        for p in sorted(papers, key=lambda p: -(p.get("upvotes") or 0))[:n]:
            title = re.sub(r"\s+", " ", p["title"]).strip()
            out.append({
                "kind": "paper", "topic": title, "upvotes": p.get("upvotes") or 0,
                "context": (p.get("summary") or "")[:220].strip(),
                "link": f"https://huggingface.co/papers/{p['id']}",
                "question": f"What does the new AI research paper \"{title}\" propose, and why does it matter?",
                "focus": "academic",
            })
    except Exception as e:  # noqa: BLE001
        print("hugging face daily papers failed:", e)
    if out:
        return out
    try:   # fallback: newest arXiv submissions in the main AI categories (no attention signal)
        from app.sources.arxiv import parse_arxiv
        r = await c.get("https://export.arxiv.org/api/query", params={
            "search_query": "cat:cs.AI OR cat:cs.CL OR cat:cs.LG OR cat:cs.CV",
            "sortBy": "submittedDate", "sortOrder": "descending", "max_results": str(n)})
        for d in parse_arxiv(r.text)[:n]:
            out.append({"kind": "paper", "topic": d.title, "context": (d.snippet or "")[:220], "link": d.url,
                        "question": f"What does the new AI research paper \"{d.title}\" propose, and why does it matter?",
                        "focus": "academic"})
    except Exception as e:  # noqa: BLE001
        print("arxiv fallback failed:", e)
    return out


async def wiki_tech_topics(c: httpx.AsyncClient, day: dt.date, n: int) -> list[dict]:
    ref = day - dt.timedelta(days=1)   # most-read is published for the previous day
    r = await c.get(f"https://en.wikipedia.org/api/rest_v1/feed/featured/{ref:%Y/%m/%d}")
    r.raise_for_status()
    out = []
    for a in (r.json().get("mostread") or {}).get("articles", []):
        if SKIP_WIKI.search(a.get("title", "")) or a.get("type", "standard") != "standard":
            continue
        name = a.get("normalizedtitle") or a["title"].replace("_", " ")
        desc = a.get("description", "")
        if not is_tech(name, desc):
            continue
        out.append({
            "kind": "wikipedia", "topic": name, "views": a.get("views"), "context": desc,
            "link": f"https://en.wikipedia.org/wiki/{a['title']}",
            "question": f"Who or what is {name}, and what are the key facts to know?", "focus": "wiki",
        })
        if len(out) >= n:
            break
    return out


async def gather(day: dt.date, counts: dict[str, int], user_agent: str, github_token: str = "") -> list[dict]:
    """Collect topics from every source; a failing source is logged and skipped."""
    topics: list[dict] = []
    async with httpx.AsyncClient(timeout=20, headers={"User-Agent": user_agent}, follow_redirects=True) as c:
        jobs = [("hackernews", lambda: hn_topics(c, counts.get("hn", 3))),
                ("github", lambda: github_topics(c, day, counts.get("github", 2), github_token)),
                ("paper", lambda: paper_topics(c, counts.get("papers", 2))),
                ("wikipedia", lambda: wiki_tech_topics(c, day, counts.get("wiki", 2)))]
        key = {"hackernews": "hn", "github": "github", "paper": "papers", "wikipedia": "wiki"}
        for name, job in jobs:
            if counts.get(key[name], 1) <= 0:
                continue
            try:
                topics += await job()
            except Exception as e:  # noqa: BLE001
                print(f"{name} trending failed:", e)
    seen, uniq = set(), []
    for t in topics:
        k = _norm(t["topic"])
        if k and k not in seen:
            seen.add(k)
            uniq.append(t)
    return uniq


# --------------------------------------------------------------- classify
CLASSIFY_PROMPT = (
    "Classify each trending tech item into exactly one category. Categories: "
    + ", ".join(f"{k} ({v})" for k, v in LABELS.items())
    + ". Reply with ONLY a JSON object mapping the item number to the category slug, e.g. {\"1\": \"ai\"}."
)


def parse_categories(text: str, n: int) -> dict[int, str]:
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return {}
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return {}
    out = {}
    for k, v in data.items():
        try:
            i = int(k)
        except (TypeError, ValueError):
            continue
        slug = str(v).strip().lower()
        if 1 <= i <= n and slug in CATEGORIES:
            out[i] = slug
    return out


async def classify(topics: list[dict], nv=None, model: str | None = None) -> str:
    """Sets topic['category'] on every topic. Returns which method won: 'nvidia', 'mixed' or 'keywords'."""
    got: dict[int, str] = {}
    if nv is not None and getattr(nv, "enabled", False) and topics:
        lines = "\n".join(f"{i}. [{KIND_LABEL.get(t['kind'], t['kind'])}] {t['topic']} — {t.get('context', '')[:160]}"
                          for i, t in enumerate(topics, 1))
        try:
            text = await nv.chat([{"role": "system", "content": CLASSIFY_PROMPT}, {"role": "user", "content": lines}],
                                 model=model, temperature=0.0, max_tokens=300)
            got = parse_categories(text, len(topics))
        except Exception as e:  # noqa: BLE001
            print("NVIDIA category classification failed, using keyword rules:", e)
    for i, t in enumerate(topics, 1):
        t["category"] = got.get(i) or fallback_category(t)
        t["category_by"] = "nvidia" if i in got else "keywords"
        t["signal"] = signal_text(t)
    if got and len(got) == len(topics):
        return "nvidia"
    return "mixed" if got else "keywords"
