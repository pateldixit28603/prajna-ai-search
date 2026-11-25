# Prajna — Open-Source AI Answer Engine (powered by NVIDIA NIM)

Prajna (Sanskrit: *wisdom*) is a Perplexity-style AI search engine. You ask a question in English, Hindi or Hinglish. Prajna searches open data sources, ranks the passages with NVIDIA NeMo Retriever models and streams back a grounded answer, with a numbered citation on every claim.

![stack](https://img.shields.io/badge/backend-FastAPI-009688) ![stack](https://img.shields.io/badge/frontend-React%20%2B%20Vite-61dafb) ![nvidia](https://img.shields.io/badge/AI-NVIDIA%20NIM-76b900) ![data](https://img.shields.io/badge/data-100%25%20open-blue)

---

## What it does

| Feature | How |
|---|---|
| **Conversational search** | Threads with follow-ups; the LLM rewrites "its price?" into a standalone query |
| **Open data sources** | Wikipedia (any language, auto-Hindi for Devanagari), OpenAlex (250M+ papers, CC0), arXiv, Hacker News, plus your own local index |
| **Hybrid retrieval** | BM25 (lexical) ⊕ NVIDIA `llama-3.2-nv-embedqa-1b-v2` embeddings (semantic), fused with Reciprocal Rank Fusion |
| **Neural reranking** | NVIDIA `llama-3.2-nv-rerankqa-1b-v2` cross-encoder picks the best passages |
| **Grounded answers** | NVIDIA Nemotron LLM streams Markdown answers with `[n]` citations (reasoning `<think>` blocks are filtered out) |
| **Focus modes** | All · Encyclopedia · Academic · Tech · My index |
| **Local knowledge base** | Ingest the Simple-English Wikipedia dump, chosen Wikipedia articles, or your own `.md/.txt/.jsonl` |
| **Runs anywhere** | Hosted NVIDIA API (no GPU) **or** fully self-hosted NIM containers on your own GPU |
| **Graceful degradation** | No key? It still works in *extractive mode* (cited sentence extraction) |

## Architecture

```mermaid
flowchart LR
    U[User / React UI] -- SSE stream --> API[FastAPI /api/search]
    API --> P1[1. Query planning<br/>NIM fast LLM]
    P1 --> P2[2. Parallel fan-out]
    P2 --> W[Wikipedia] & OA[OpenAlex] & AX[arXiv] & HN[Hacker News] & LI[(Local index<br/>BM25 + vectors)]
    W & OA & AX & HN & LI --> P3[3. Chunk passages]
    P3 --> P4[4. Hybrid rank<br/>BM25 ⊕ NeMo embeddings · RRF]
    P4 --> P5[5. NeMo reranker]
    P5 --> P6[6. Nemotron LLM<br/>cited answer, streamed]
    P6 --> P7[7. Follow-up questions]
    P7 --> DB[(SQLite threads)]
```

```
prajna/
├── backend/
│   ├── app/
│   │   ├── main.py            FastAPI app, SSE search endpoint, threads API, serves built UI
│   │   ├── pipeline.py        the 7-stage answer engine
│   │   ├── nvidia.py          NIM client: chat stream, embeddings, rerank, <think> filter
│   │   ├── prompts.py         all prompts in one place
│   │   ├── fallback.py        extractive answers when no NVIDIA endpoint is configured
│   │   ├── store.py           SQLite conversation history
│   │   ├── ratelimit.py       per-IP sliding-window limiter
│   │   ├── sources/           wikipedia.py, openalex.py, arxiv.py, hackernews.py
│   │   └── retrieval/         bm25.py, fusion.py (RRF, cosine, MMR), text.py, local_index.py
│   ├── scripts/ingest.py      build the local open-data index
│   └── tests/                 15 tests, all NVIDIA + network calls mocked
├── frontend/                  React 18 + TypeScript + Tailwind v4
├── deploy/docker-compose.gpu.yml   self-hosted NIM LLM + embed + rerank on your GPU
├── docker-compose.yml         app with hosted NVIDIA API
└── Dockerfile                 multi-stage: builds UI, serves it from FastAPI
```

## Quick start (local dev)

**Requirements:** Python 3.11+, Node 20+, and a free NVIDIA API key from [build.nvidia.com](https://build.nvidia.com). Click a model, then **Get API Key**. The key starts with `nvapi-`.

```bash
cp .env.example .env              # paste your NVIDIA_API_KEY
make install                      # venv + npm install
make dev-api                      # terminal 1 -> http://localhost:8000
make dev-web                      # terminal 2 -> http://localhost:5173
```

Optional: build a local knowledge base.

```bash
make ingest-demo                                                  # a few full Wikipedia articles
cd backend && .venv/bin/python -m scripts.ingest hf-wikipedia --limit 20000   # Simple English Wikipedia dump (Hugging Face)
cd backend && .venv/bin/python -m scripts.ingest files ~/my-notes            # your own .md/.txt/.jsonl
```

## Production (Docker)

```bash
docker compose up --build                                   # hosted NVIDIA API, no GPU needed
docker compose -f deploy/docker-compose.gpu.yml up --build  # 100% self-hosted on your NVIDIA GPU
```

The GPU stack runs three NIM containers (`llama-3.1-8b-instruct`, `llama-3.2-nv-embedqa-1b-v2`, `llama-3.2-nv-rerankqa-1b-v2`). It needs the NVIDIA Container Toolkit and an NGC key. The app talks to them over the same OpenAI-compatible APIs, so you don't change any code. Only the env vars change.

## Where NVIDIA is used

| Stage | Model (default, configurable) | Endpoint |
|---|---|---|
| Query planning + follow-ups | `nvidia/llama-3.1-nemotron-nano-8b-v1` | `POST /v1/chat/completions` |
| Answer generation (streaming) | `nvidia/nemotron-3-nano-30b-a3b` | `POST /v1/chat/completions` (`stream: true`) |
| Passage + query embeddings | `nvidia/llama-3.2-nv-embedqa-1b-v2` | `POST /v1/embeddings` (`input_type: query/passage`) |
| Reranking | `nvidia/llama-3.2-nv-rerankqa-1b-v2` | hosted `…/retrieval/…/reranking` or local `/v1/ranking` |

You can swap in a bigger answer model by setting `LLM_MODEL`, for example `nvidia/llama-3.1-nemotron-ultra-253b-v1`. Any chat model listed at build.nvidia.com works.

## API

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | NVIDIA status, models, local-index stats, focus modes |
| `POST` | `/api/search` | `{query, focus, thread_id?}` → **SSE** events: `status`, `queries`, `sources`, `token`, `followups`, `done`, `error` |
| `GET` | `/api/threads` | recent threads |
| `GET` | `/api/threads/{id}` | full thread with turns, sources, timings |
| `DELETE` | `/api/threads/{id}` | delete thread |

Interactive docs: `http://localhost:8000/docs`.

## Tests

```bash
make test     # 15 tests: parsers, BM25, RRF, MMR, chunker, <think> filter, NVIDIA path (mocked), SSE API, threads
```

## Data sources and licenses

| Source | License | Notes |
|---|---|---|
| Wikipedia | CC BY-SA 4.0 | Attribution is shown in the source cards. Set `CONTACT_EMAIL` per the Wikimedia User-Agent policy |
| OpenAlex | CC0 | Uses the polite pool via `mailto` |
| arXiv | per-paper | API terms: keep request rates low |
| Hacker News (Algolia) | public API | |

## Roadmap ideas

- Swap the NumPy vector store for Milvus with NVIDIA cuVS (GPU vector search) above roughly 1M chunks
- Add NemoGuard content-safety and jailbreak-detection NIMs as input/output rails
- Image search via Wikimedia Commons; multimodal answers with a VLM NIM
- Redis-backed rate limiting and caching for multi-instance deploys
- User accounts and shareable thread links
