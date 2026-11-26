"""Prajna — open-source AI answer engine. FastAPI entrypoint.

Run:  uvicorn app.main:app --reload --port 8000
"""
from __future__ import annotations

import json
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import lang as L
from .config import settings
from .nvidia import NvidiaClient
from .imagegen import ASPECTS, ImageError, ImageGenerator
from .pipeline import FOCUS_MODES, AnswerEngine
from .ratelimit import RateLimiter
from .research import ResearchService
from .retrieval.local_index import LocalIndex
from .sources.arxiv import ArxivSource
from .sources.hackernews import HackerNewsSource
from .sources.openalex import OpenAlexSource
from .sources.wikipedia import WikipediaSource
from .store import ThreadStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("prajna")


def build_engine(http: httpx.AsyncClient) -> tuple[AnswerEngine, LocalIndex]:
    nv = NvidiaClient(settings)
    ua, to = settings.user_agent, settings.http_timeout
    local = LocalIndex(settings.data_dir / "index", embedder=nv)
    sources = {
        "wikipedia": WikipediaSource(http, ua, to),
        "openalex": OpenAlexSource(http, ua, to, mailto=settings.contact_email),
        "arxiv": ArxivSource(http, ua, to),
        "hackernews": HackerNewsSource(http, ua, to),
        "local": local,
    }
    return AnswerEngine(settings, nv, sources), local


@asynccontextmanager
async def lifespan(app: FastAPI):
    http = httpx.AsyncClient(follow_redirects=True, limits=httpx.Limits(max_connections=40))
    if not getattr(app.state, "engine", None):          # tests may inject their own engine
        app.state.engine, app.state.local = build_engine(http)
    if not getattr(app.state, "research", None):
        app.state.research = ResearchService(http, settings.user_agent, settings.contact_email, settings.http_timeout)
    if not getattr(app.state, "images", None):
        app.state.images = ImageGenerator(settings)
    if not getattr(app.state, "store", None):
        app.state.store = ThreadStore(settings.data_dir / "prajna.db")
    log.info("NVIDIA NIM %s | LLM=%s", "ENABLED" if settings.nvidia_enabled else "DISABLED (extractive mode)",
             settings.llm_model)
    yield
    await http.aclose()


app = FastAPI(title="Prajna AI Search", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=False,
                   allow_methods=["*"], allow_headers=["*"])
limiter = RateLimiter(per_minute=30)
image_limiter = RateLimiter(per_minute=6)


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    focus: str = "all"
    thread_id: str | None = None
    lang: str | None = None          # answer language; None/"auto" = thread's choice, else detected


class ImageRequest(BaseModel):
    prompt: str = Field(..., min_length=2, max_length=1000)
    aspect: str = "square"
    enhance: bool = True               # let Nemotron Bolt expand the idea into a detailed prompt
    seed: int | None = Field(None, ge=0, le=2**31 - 1)
    thread_id: str | None = None


class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=12000)
    lang: str
    n_sources: int = Field(0, ge=0, le=50)
    turn_id: int | None = None       # when given, the translation is cached on the stored turn
    thread_id: str | None = None     # when given, the language becomes the thread's choice


def sse(event: dict) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


# ------------------------------------------------------------------- routes
@app.get("/api/health")
async def health(request: Request):
    local: LocalIndex | None = getattr(request.app.state, "local", None)
    return {
        "status": "ok",
        "nvidia": settings.nvidia_enabled,
        "models": {"llm": settings.llm_model, "fast": settings.llm_fast_model,
                   "embed": settings.embed_model, "rerank": settings.rerank_model},
        "local_index": local.stats() if local else None,
        "focus_modes": {k: v["label"] for k, v in FOCUS_MODES.items()},
        "image_models": settings.image_models,
        "languages": {k: {"label": v["label"], "native": v["native"], "dir": v["dir"]} for k, v in L.LANGUAGES.items()},
    }


@app.post("/api/search")
async def search(req: SearchRequest, request: Request):
    client_ip = request.client.host if request.client else "anon"
    if not limiter.allow(client_ip):
        raise HTTPException(429, "Too many searches — slow down a little.")
    if req.focus not in FOCUS_MODES:
        raise HTTPException(400, f"Unknown focus mode. Use one of {list(FOCUS_MODES)}")

    engine: AnswerEngine = request.app.state.engine
    store: ThreadStore = request.app.state.store
    query = req.query.strip()
    thread_id = req.thread_id if req.thread_id and store.exists(req.thread_id) else None
    history = store.history(thread_id) if thread_id else []
    lang = L.normalize(req.lang) or (store.get_lang(thread_id) if thread_id else None) or L.detect_language(query)
    lang_source = "chosen" if L.normalize(req.lang) else "thread" if thread_id and store.get_lang(thread_id) else "detected"

    async def events():
        nonlocal thread_id
        t0 = time.perf_counter()
        try:
            yield sse({"type": "status", "stage": "planning", "message": "Understanding your question…"})
            yield sse({"type": "lang", "lang": lang, "source": lang_source})
            res = await engine.retrieve(query, req.focus, history, lang)
            yield sse({"type": "queries", "queries": res.queries})
            yield sse({"type": "status", "stage": "reading",
                       "message": f"Reading {len(res.sources)} sources…"})
            public_sources = [d.to_public() | {"n": i + 1} for i, d in enumerate(res.sources)]
            yield sse({"type": "sources", "sources": public_sources, "warnings": res.warnings})
            yield sse({"type": "status", "stage": "writing", "message": "Writing answer…"})

            parts: list[str] = []
            t_first = None
            async for tok in engine.answer_stream(res, history, lang):
                if t_first is None:
                    t_first = time.perf_counter() - t0
                parts.append(tok)
                yield sse({"type": "token", "text": tok})
            answer = "".join(parts)
            repaired = engine.repair_citations(answer, res)
            if repaired != answer:
                answer = repaired
                yield sse({"type": "replace", "text": answer})

            follow = await engine.followups(query, answer, res, lang)
            yield sse({"type": "followups", "questions": follow})

            if not thread_id:
                thread_id = store.create_thread(query, req.focus, lang)
            elif L.normalize(req.lang):
                store.set_lang(thread_id, lang)
            meta = {"queries": res.queries, "timings": res.timings, "focus": req.focus, "lang": lang,
                    "nvidia": bool(settings.nvidia_enabled and engine.last_llm_ok), "ttft": t_first, "total": time.perf_counter() - t0}
            turn_id = store.add_turn(thread_id, query, answer, public_sources, follow, meta)
            yield sse({"type": "done", "thread_id": thread_id, "turn_id": turn_id, "meta": meta})
        except Exception as e:  # never leave the client hanging
            log.exception("search failed")
            yield sse({"type": "error", "message": f"Search failed: {type(e).__name__}"})

    return StreamingResponse(events(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/api/research")
async def research(q: str, request: Request):
    """Literature map for a topic: key, foundational and rising papers, read-next list, timeline (OpenAlex)."""
    q = q.strip()[:300]
    if len(q) < 2:
        raise HTTPException(400, "Query too short")
    client_ip = request.client.host if request.client else "anon"
    if not limiter.allow(client_ip):
        raise HTTPException(429, "Too many requests — slow down a little.")
    try:
        return await request.app.state.research.explore(q)
    except Exception as e:
        log.warning("research failed: %s", e)
        raise HTTPException(502, "OpenAlex is unreachable right now. Try again in a moment.")


@app.post("/api/image")
async def create_image(req: ImageRequest, request: Request):
    """Generate an image with NVIDIA visual GenAI (FLUX / Stable Diffusion), saved into a thread."""
    if req.aspect not in ASPECTS:
        raise HTTPException(400, f"Unknown aspect. Use one of {list(ASPECTS)}")
    client_ip = request.client.host if request.client else "anon"
    if not image_limiter.allow(client_ip):
        raise HTTPException(429, "Image limit reached (6 per minute). Wait a moment.")
    gen: ImageGenerator = request.app.state.images
    engine: AnswerEngine = request.app.state.engine
    store: ThreadStore = request.app.state.store
    idea = req.prompt.strip()
    t0 = time.perf_counter()
    prompt = await gen.enhance(engine.nv, idea) if req.enhance else idea
    try:
        out = await gen.generate(prompt, req.aspect, req.seed)
    except ImageError as e:
        raise HTTPException(e.status, str(e))
    meta = {"kind": "image", "image": out["image"], "model": out["model"], "seed": out["seed"],
            "aspect": out["aspect"], "prompt": prompt, "enhanced": prompt != idea,
            "total": time.perf_counter() - t0, "nvidia": True}
    thread_id = req.thread_id if req.thread_id and store.exists(req.thread_id) else None
    if not thread_id:
        thread_id = store.create_thread(f"🎨 {idea}", "image")
    turn_id = store.add_turn(thread_id, idea, "", [], [], meta)
    return meta | {"idea": idea, "thread_id": thread_id, "turn_id": turn_id}


@app.post("/api/translate")
async def translate(req: TranslateRequest, request: Request):
    """Re-render an answer in one of the 7 answer languages. No new search; citations are preserved."""
    lang = L.normalize(req.lang)
    if not lang:
        raise HTTPException(400, f"Unknown language. Use one of {list(L.LANGUAGES)}")
    client_ip = request.client.host if request.client else "anon"
    store: ThreadStore = request.app.state.store
    engine: AnswerEngine = request.app.state.engine
    turn = store.get_turn(req.turn_id) if req.turn_id else None
    if turn and req.thread_id and turn["thread_id"] != req.thread_id:
        turn = None
    cached = (turn or {}).get("meta", {}).get("translations", {}).get(lang)
    if cached:
        text, ok, msg = cached, True, ""
    else:
        if not limiter.allow(client_ip):
            raise HTTPException(429, "Too many requests — slow down a little.")
        source_text = turn["answer"] if turn else req.text
        n_sources = len(turn["sources"]) if turn else req.n_sources
        if turn and lang == turn["meta"].get("lang"):
            text, ok, msg = source_text, True, ""
        else:
            text, ok, msg = await engine.translate(source_text, lang, n_sources)
        if ok and turn:
            store.save_translation(turn["id"], lang, text)
    if ok and req.thread_id and store.exists(req.thread_id):
        store.set_lang(req.thread_id, lang)
    return {"lang": lang, "dir": L.LANGUAGES[lang]["dir"], "text": text, "ok": ok, "message": msg,
            "citations_ok": L.citations_preserved(turn["answer"] if turn else req.text, text)}


@app.get("/api/threads")
async def list_threads(request: Request):
    return request.app.state.store.list_threads()


@app.get("/api/threads/{tid}")
async def get_thread(tid: str, request: Request):
    t = request.app.state.store.get_thread(tid)
    if not t:
        raise HTTPException(404, "Thread not found")
    return t


@app.delete("/api/threads/{tid}")
async def delete_thread(tid: str, request: Request):
    if not request.app.state.store.delete_thread(tid):
        raise HTTPException(404, "Thread not found")
    return {"deleted": tid}


# ------------------------------------------------- serve built frontend (prod)
DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    async def spa(path: str):
        f = DIST / path
        return FileResponse(f if path and f.is_file() else DIST / "index.html")
