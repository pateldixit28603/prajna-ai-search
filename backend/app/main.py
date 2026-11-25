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

from .config import settings
from .nvidia import NvidiaClient
from .pipeline import FOCUS_MODES, AnswerEngine
from .ratelimit import RateLimiter
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


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    focus: str = "all"
    thread_id: str | None = None


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

    async def events():
        nonlocal thread_id
        t0 = time.perf_counter()
        try:
            yield sse({"type": "status", "stage": "planning", "message": "Understanding your question…"})
            res = await engine.retrieve(query, req.focus, history)
            yield sse({"type": "queries", "queries": res.queries})
            yield sse({"type": "status", "stage": "reading",
                       "message": f"Reading {len(res.sources)} sources…"})
            public_sources = [d.to_public() | {"n": i + 1} for i, d in enumerate(res.sources)]
            yield sse({"type": "sources", "sources": public_sources, "warnings": res.warnings})
            yield sse({"type": "status", "stage": "writing", "message": "Writing answer…"})

            parts: list[str] = []
            t_first = None
            async for tok in engine.answer_stream(res, history):
                if t_first is None:
                    t_first = time.perf_counter() - t0
                parts.append(tok)
                yield sse({"type": "token", "text": tok})
            answer = "".join(parts)

            follow = await engine.followups(query, answer, res)
            yield sse({"type": "followups", "questions": follow})

            if not thread_id:
                thread_id = store.create_thread(query, req.focus)
            meta = {"queries": res.queries, "timings": res.timings, "focus": req.focus,
                    "nvidia": settings.nvidia_enabled, "ttft": t_first, "total": time.perf_counter() - t0}
            store.add_turn(thread_id, query, answer, public_sources, follow, meta)
            yield sse({"type": "done", "thread_id": thread_id, "meta": meta})
        except Exception as e:  # never leave the client hanging
            log.exception("search failed")
            yield sse({"type": "error", "message": f"Search failed: {type(e).__name__}"})

    return StreamingResponse(events(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


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
