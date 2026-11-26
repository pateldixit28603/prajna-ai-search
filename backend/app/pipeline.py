"""The answer-engine pipeline.

   question ──► 1. query planning (NIM LLM rewrites into search queries)
            ──► 2. parallel fan-out to open-data sources (Wikipedia, arXiv, OpenAlex, HN, local index)
            ──► 3. chunk documents into passages
            ──► 4. hybrid first-stage ranking  (BM25 ⊕ NeMo Retriever embeddings, RRF fusion)
            ──► 5. NeMo Retriever reranker (cross-encoder) picks the best passages
            ──► 6. grounded, cited answer streamed from the NIM LLM
            ──► 7. follow-up question suggestions
Each stage degrades gracefully if NVIDIA is unavailable, so the engine never hard-fails.
"""
from __future__ import annotations

import asyncio
import datetime as dt
import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import AsyncIterator

from .config import Settings
from . import lang as L
from .fallback import extractive_answer, heuristic_followups
from .nvidia import NvidiaClient
from .prompts import ANSWER_SYSTEM, ANSWER_USER, FOLLOWUP_SYSTEM, REWRITE_SYSTEM
from .retrieval.bm25 import BM25
from .retrieval.fusion import argsort_desc, cosine, rrf
from .retrieval.text import chunk_text
from .sources.base import Document

log = logging.getLogger("prajna.pipeline")

FOCUS_MODES: dict[str, dict] = {
    "all":      {"label": "All",      "sources": ["wikipedia", "openalex", "arxiv", "hackernews", "local"]},
    "wiki":     {"label": "Encyclopedia", "sources": ["wikipedia", "local"]},
    "academic": {"label": "Academic", "sources": ["openalex", "arxiv"]},
    "tech":     {"label": "Tech news", "sources": ["hackernews", "arxiv"]},
    "local":    {"label": "My index", "sources": ["local"]},
}


@dataclass
class Passage:
    doc: Document
    text: str
    score: float = 0.0


@dataclass
class SearchResult:
    question: str
    queries: list[str]
    sources: list[Document]
    passages: list[Passage]
    warnings: list[str] = field(default_factory=list)
    timings: dict[str, float] = field(default_factory=dict)


def _json_from(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return {}


class AnswerEngine:
    def __init__(self, settings: Settings, nvidia: NvidiaClient, sources: dict):
        self.s = settings
        self.nv = nvidia
        self.sources = sources          # name -> SearchSource
        self.last_llm_ok = False        # did the most recent answer really come from the LLM?
        self.last_llm_error = ""

    # ------------------------------------------------------------ 1. planning
    async def plan_queries(self, question: str, history: list[dict]) -> list[str]:
        if not (self.s.use_query_rewrite and self.nv.enabled):
            return [question]
        hist = "\n".join(f"User: {h['question']}\nAssistant: {h['answer'][:300]}" for h in history[-2:])
        msg = f"History:\n{hist or '(none)'}\n\nLatest message: {question}"
        try:
            raw = await asyncio.wait_for(self.nv.chat(
                [{"role": "system", "content": REWRITE_SYSTEM}, {"role": "user", "content": msg}],
                model=self.s.llm_fast_model, temperature=0.0, max_tokens=120), timeout=8)
            qs = [q.strip() for q in _json_from(raw).get("queries", []) if isinstance(q, str) and q.strip()]
            return qs[:3] or [question]
        except Exception as e:
            log.warning("query rewrite failed: %s", e)
            return [question]

    # ------------------------------------------------------------ 2. fan-out
    async def gather(self, queries: list[str], focus: str,
                     native: tuple[str, str] | None = None) -> tuple[list[Document], list[str]]:
        """Fan out to every source. `native` = (wiki edition, original question): for a non-English
        answer language, the matching Wikipedia edition (ru.wikipedia.org, …) is searched too."""
        names = [n for n in FOCUS_MODES.get(focus, FOCUS_MODES["all"])["sources"] if n in self.sources]
        warnings: list[str] = []

        async def run(name: str, q: str):
            try:
                return await asyncio.wait_for(self.sources[name].search(q, self.s.per_source_limit),
                                              timeout=self.s.http_timeout)
            except Exception as e:
                warnings.append(f"{name}: {type(e).__name__}")
                return []

        async def run_native(edition: str, q: str):
            try:
                return await asyncio.wait_for(
                    self.sources["wikipedia"].search_edition(q, self.s.per_source_limit, edition),
                    timeout=self.s.http_timeout)
            except Exception as e:
                warnings.append(f"wikipedia-{edition}: {type(e).__name__}")
                return []

        tasks = [run(n, q) for n in names for q in queries]
        if native and "wikipedia" in names and hasattr(self.sources["wikipedia"], "search_edition"):
            tasks.append(run_native(*native))
        results = await asyncio.gather(*tasks)
        docs, seen = [], set()
        for batch in results:
            for d in batch:
                key = d.url.rstrip("/").lower()
                if key in seen:
                    continue
                seen.add(key)
                docs.append(d)
        return docs, sorted(set(warnings))

    # ------------------------------------------------------- 3-5. ranking
    async def rank(self, question: str, queries: list[str], docs: list[Document]) -> tuple[list[Passage], dict]:
        info: dict = {"dense": False, "rerank": False}
        passages: list[Passage] = []
        for d in docs:
            for ch in chunk_text(d.content, self.s.chunk_words, self.s.chunk_overlap)[:6]:
                passages.append(Passage(doc=d, text=ch))
        if not passages:
            return [], info

        texts = [f"{p.doc.title}. {p.text}" for p in passages]
        query_text = " ".join(dict.fromkeys([question, *queries]))
        rankings = [argsort_desc(BM25(texts).scores(query_text))]

        if self.s.use_dense and self.nv.enabled:
            try:
                import numpy as np
                vecs = await self.nv.embed(texts, input_type="passage")
                qv = (await self.nv.embed([question], input_type="query"))[0]
                rankings.append(argsort_desc(cosine(qv, np.asarray(vecs, dtype=np.float32))))
                info["dense"] = True
            except Exception as e:
                log.warning("dense ranking failed: %s", e)

        fused = sorted(rrf(rankings).items(), key=lambda kv: -kv[1])
        candidates = [passages[i] for i, _ in fused[:40]]
        for (i, sc), p in zip(fused[:40], candidates):
            p.score = sc

        if self.s.use_rerank and self.nv.enabled and len(candidates) > 1:
            try:
                logits = await self.nv.rerank(question, [f"{p.doc.title}. {p.text}" for p in candidates])
                for p, lg in zip(candidates, logits):
                    p.score = lg
                candidates.sort(key=lambda p: -p.score)
                info["rerank"] = True
            except Exception as e:
                log.warning("rerank failed: %s", e)
        return candidates, info

    def select(self, passages: list[Passage]) -> tuple[list[Document], list[Passage]]:
        """Pick up to max_sources distinct documents, max 2 passages each, in score order."""
        docs: list[Document] = []
        per_doc: dict[str, int] = {}
        chosen: list[Passage] = []
        for p in passages:
            did = p.doc.id
            if did not in per_doc:
                if len(docs) >= self.s.max_sources:
                    continue
                docs.append(p.doc)
                per_doc[did] = 0
            if per_doc[did] < 2:
                per_doc[did] += 1
                chosen.append(p)
        return docs, chosen

    async def retrieve(self, question: str, focus: str, history: list[dict],
                       lang: str | None = None) -> SearchResult:
        t0 = time.perf_counter()
        queries = await self.plan_queries(question, history)
        t1 = time.perf_counter()
        edition = L.wiki_edition(lang or L.detect_language(question))
        docs, warnings = await self.gather(queries, focus, (edition, question) if edition else None)
        t2 = time.perf_counter()
        ranked, info = await self.rank(question, queries, docs)
        t3 = time.perf_counter()
        sources, passages = self.select(ranked)
        res = SearchResult(question, queries, sources, passages, warnings,
                           {"plan": t1 - t0, "search": t2 - t1, "rank": t3 - t2})
        res.timings |= {k: float(v) for k, v in info.items()}
        return res

    # --------------------------------------------------------- 6. answering
    def build_context(self, res: SearchResult) -> tuple[str, list[tuple[int, str]]]:
        num = {d.id: i + 1 for i, d in enumerate(res.sources)}
        blocks: dict[int, list[str]] = {}
        for p in res.passages:
            blocks.setdefault(num[p.doc.id], []).append(p.text)
        ctx, flat = [], []
        for d in res.sources:
            n = num[d.id]
            body = " … ".join(blocks.get(n, []))
            meta = ", ".join(x for x in [d.source, d.published or ""] if x)
            ctx.append(f"[{n}] {d.title} ({meta})\nURL: {d.url}\n{body}")
            flat.extend((n, t) for t in blocks.get(n, []))
        return "\n\n".join(ctx), flat

    async def answer_stream(self, res: SearchResult, history: list[dict],
                            lang: str | None = None) -> AsyncIterator[str]:
        context, flat = self.build_context(res)
        if not res.sources:
            yield ("I couldn't find anything relevant in the open sources for this question. "
                   "Try different keywords or another focus mode.")
            return
        if not self.nv.enabled:
            text = extractive_answer(res.question, flat)
            for piece in re.findall(r"\S+\s*", text):
                yield piece
                await asyncio.sleep(0.004)
            return
        messages = [{"role": "system", "content": ANSWER_SYSTEM.format(
            today=dt.date.today().isoformat(), lang_rule=L.language_instruction(lang))}]
        for h in history[-3:]:
            messages += [{"role": "user", "content": h["question"]},
                         {"role": "assistant", "content": h["answer"][:1500]}]
        messages.append({"role": "user", "content": ANSWER_USER.format(context=context, question=res.question)})
        self.last_llm_ok = False
        got_any = False
        try:
            async for tok in self.nv.chat_stream(messages):
                got_any = True
                yield tok
            self.last_llm_ok = got_any
        except Exception as e:
            log.error("LLM stream failed, falling back to extractive: %s", e)
            self.last_llm_error = str(e)[:300]
        if not self.last_llm_ok:
            yield ("\n\n" if got_any else "") + extractive_answer(res.question, flat)

    # ---------------------------------------------------- 6b. citation repair
    def repair_citations(self, answer: str, res: SearchResult, min_overlap: float = 0.5) -> str:
        """Attach a citation to uncited factual sentences when one source clearly supports them.

        Purely lexical and conservative: a sentence gets [n] only if >= min_overlap of its content words
        appear in source n's retrieved passages. Unsupported sentences stay uncited (and are measured as such).
        """
        if not res.sources:
            return answer
        from .retrieval.text import tokenize
        num = {d.id: i + 1 for i, d in enumerate(res.sources)}
        support: dict[int, set[str]] = {}
        for p in res.passages:
            support.setdefault(num[p.doc.id], set()).update(tokenize(f"{p.doc.title} {p.text}"))
        out_lines = []
        for line in answer.split("\n"):
            stripped = line.strip()
            if not stripped or stripped.startswith(("#", "|", ">", "```")):
                out_lines.append(line)
                continue
            parts = re.split(r"(?<=[.!?।])(\s+)(?!\[\d)", line)
            fixed = []
            for part in parts:
                if (not part.strip() or re.search(r"\[\d{1,2}\]", part) or len(part.split()) < 6
                        or re.search(r"(?:^|\s)(?:[A-Z]|Dr|Mr|Mrs|Ms|St|vs|etc|e\.g|i\.e)\.\s*$", part)):
                    fixed.append(part)
                    continue
                words = set(tokenize(part))
                best, score = None, 0.0
                for n, vocab in support.items():
                    sc = len(words & vocab) / (len(words) or 1)
                    if sc > score:
                        best, score = n, sc
                if best and score >= min_overlap:
                    m = re.match(r"^(.*?)([.!?।]?)(\s*)$", part, re.S)
                    part = f"{m.group(1)} [{best}]{m.group(2)}{m.group(3)}"
                fixed.append(part)
            out_lines.append("".join(fixed))
        return "\n".join(out_lines)

    # -------------------------------------------------------- 7. follow-ups
    async def followups(self, question: str, answer: str, res: SearchResult,
                        lang: str | None = None) -> list[str]:
        titles = [d.title for d in res.sources]
        if not self.nv.enabled:
            return heuristic_followups(question, titles)
        try:
            raw = await asyncio.wait_for(self.nv.chat(
                [{"role": "system", "content": FOLLOWUP_SYSTEM.replace(
                    "LANG_RULE", L.language_instruction(lang).replace("whole answer", "questions"))},
                 {"role": "user", "content": f"Question: {question}\nAnswer summary: {answer[:800]}"}],
                model=self.s.llm_fast_model, temperature=0.5, max_tokens=150), timeout=8)
            qs = [q.strip() for q in _json_from(raw).get("questions", []) if isinstance(q, str)]
            return qs[:3] or heuristic_followups(question, titles)
        except Exception:
            return heuristic_followups(question, titles)

    # ------------------------------------------------- 8. answer translation
    async def translate(self, text: str, lang: str, n_sources: int) -> tuple[str, bool, str]:
        """Re-render an answer in another language with the NIM LLM (no new search).

        Returns (text, ok, message). Citations are verified and restored, so [n] keeps pointing at
        the same source. If NVIDIA is unavailable the original text comes back with ok=False.
        """
        if lang not in L.LANGUAGES:
            return text, False, "Unsupported language"
        if not text.strip():
            return text, True, ""
        if not self.nv.enabled:
            return text, False, "Translation needs NVIDIA NIM, which isn't configured here."
        try:
            out = await asyncio.wait_for(self.nv.chat(
                [{"role": "system", "content": L.TRANSLATE_SYSTEM.format(name=L.LANGUAGES[lang]["name"])},
                 {"role": "user", "content": text}],
                temperature=0.1, max_tokens=2000), timeout=45)
        except Exception as e:
            log.warning("translation failed: %s", e)
            return text, False, "NVIDIA NIM translation failed. Showing the original answer."
        out = out.strip()
        if not out:
            return text, False, "NVIDIA NIM returned an empty translation. Showing the original answer."
        return L.restore_citations(text, out, n_sources), True, ""
