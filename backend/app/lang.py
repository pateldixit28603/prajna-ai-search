"""Answer languages: detection, Wikipedia editions, and citation-preserving translation.

Prajna answers in 7 languages: the five most-spoken languages in the world (Ethnologue), Russian, and
Hinglish (Hindi-English written in Latin script). An answer can be re-rendered into any of them with one
click. The NIM LLM translates; this module makes sure every [n] citation still points at the same source.
"""
from __future__ import annotations

import re
from collections import Counter

LANGUAGES: dict[str, dict] = {
    "en":       {"label": "English",  "native": "English",  "name": "English", "dir": "ltr", "wiki": "en"},
    "zh":       {"label": "Chinese",  "native": "简体中文", "name": "Simplified Chinese (简体中文)", "dir": "ltr", "wiki": "zh"},
    "hi":       {"label": "Hindi",    "native": "हिन्दी",    "name": "Hindi in Devanagari script (हिन्दी)", "dir": "ltr", "wiki": "hi"},
    "es":       {"label": "Spanish",  "native": "Español",  "name": "Spanish (Español)", "dir": "ltr", "wiki": "es"},
    "ar":       {"label": "Arabic",   "native": "العربية",  "name": "Modern Standard Arabic (العربية)", "dir": "rtl", "wiki": "ar"},
    "ru":       {"label": "Russian",  "native": "Русский",  "name": "Russian (Русский)", "dir": "ltr", "wiki": "ru"},
    "hinglish": {"label": "Hinglish", "native": "Hinglish", "name": "Hinglish: conversational Hindi-English mix written ONLY in Latin (Roman) script, never Devanagari", "dir": "ltr", "wiki": None},
}

_SCRIPTS = [
    ("hi", re.compile(r"[ऀ-ॿ]")),                    # Devanagari
    ("ru", re.compile(r"[Ѐ-ӿ]")),                    # Cyrillic
    ("ar", re.compile(r"[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]")),  # Arabic
    ("zh", re.compile(r"[一-鿿㐀-䶿]")),       # CJK ideographs
]
_HINGLISH = {"kya", "hai", "hain", "kaise", "kaisa", "kaun", "kaunsa", "kyun", "kyon", "mein", "ka", "ki", "ke",
             "hota", "hoti", "hote", "batao", "bataiye", "samjhao", "nahi", "nahin", "aur", "kab", "kitna",
             "kitne", "kahan", "tha", "thi", "matlab", "zaroori", "accha", "achha", "yeh", "woh", "kis", "kaha"}
_SPANISH = {"qué", "que", "cómo", "cuál", "cuáles", "cuándo", "dónde", "quién", "por", "para", "los", "las", "del",
            "el", "es", "son", "una", "y", "de", "la", "en", "con", "sobre", "historia", "mejor"}
_SPANISH_CHARS = re.compile(r"[ñ¿¡áéíóú]", re.I)


def normalize(lang: str | None) -> str | None:
    """Return a supported language code, or None for auto/unknown."""
    if not lang:
        return None
    lang = lang.strip().lower()
    return lang if lang in LANGUAGES else None


def detect_language(text: str) -> str:
    """Best-guess answer language for a question. Script first, then cheap word lists; English by default."""
    counts = {code: len(rx.findall(text)) for code, rx in _SCRIPTS}
    code, n = max(counts.items(), key=lambda kv: kv[1])
    if n:
        return code
    words = re.findall(r"[a-záéíóúñü]+", text.lower())
    if len({w for w in words if w in _HINGLISH}) >= 2:
        return "hinglish"
    spanish_hits = len({w for w in words if w in _SPANISH})
    if spanish_hits >= 3 or (_SPANISH_CHARS.search(text) and spanish_hits >= 1):
        return "es"
    return "en"


def wiki_edition(lang: str | None) -> str | None:
    """Extra Wikipedia language edition to search for this answer language (None = English only)."""
    ed = LANGUAGES.get(lang or "", {}).get("wiki")
    return ed if ed and ed != "en" else None


def language_instruction(lang: str | None) -> str:
    if not lang or lang not in LANGUAGES:
        return "Reply in the same language and style as the user's question."
    return f"Write the whole answer in {LANGUAGES[lang]['name']}, whatever language the sources are in."


# ------------------------------------------------------------------ citations
CITE = re.compile(r"\[(\d{1,2})\]")


def citations(text: str) -> Counter:
    return Counter(int(n) for n in CITE.findall(text))


def _paragraphs(text: str) -> list[str]:
    return [p for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]


def restore_citations(original: str, translated: str, n_sources: int) -> str:
    """Make a translation keep the original's citations.

    1. Citations that don't exist in the source list (hallucinated numbers) are dropped.
    2. Paragraph by paragraph (when the paragraph count matches), any citation the original paragraph had
       but the translation lost is appended to the end of that paragraph. Otherwise, missing ones are
       appended to the final paragraph. Numbers never change, so [n] still points at the same source.
    """
    translated = re.sub(r"\s*\[(\d{1,2})\]",
                        lambda m: m.group(0) if 1 <= int(m.group(1)) <= n_sources else "", translated)
    o_par, t_par = _paragraphs(original), _paragraphs(translated)
    if not t_par:
        return original
    pairs = list(zip(o_par, t_par)) if len(o_par) == len(t_par) else [(original, translated)]
    fixed: list[str] = []
    for o, t in pairs:
        missing = sorted(set(citations(o)) - set(citations(t)))
        if missing:
            t = _append_cites(t, missing)
        fixed.append(t)
    if len(pairs) == 1 and len(t_par) > 1:
        # whole-text fallback: put the missing citations on the last paragraph only
        missing = sorted(set(citations(original)) - set(citations(translated)))
        out = t_par[:-1] + [_append_cites(t_par[-1], missing)] if missing else t_par
        return "\n\n".join(out)
    return "\n\n".join(fixed)


def _append_cites(par: str, nums: list[int]) -> str:
    tag = "".join(f"[{n}]" for n in nums)
    m = re.match(r"^(.*?)([.!?。！？।؟]?)(\s*)$", par, re.S)
    return f"{m.group(1)} {tag}{m.group(2)}{m.group(3)}"


def citations_preserved(original: str, translated: str) -> bool:
    return set(citations(original)) <= set(citations(translated))


TRANSLATE_SYSTEM = """You are a precise translator for an AI answer engine.
Translate the user's Markdown answer into {name}.
Rules:
- Keep every citation marker like [1] or [2][3] EXACTLY as written, attached to the same sentence. Never renumber, drop or add them.
- Keep the Markdown structure (headings, bullets, tables, bold) and the same paragraphs.
- Keep names, numbers, dates, units and code unchanged; transliterate names only if natural.
- Output ONLY the translated answer, with no preamble or notes."""
