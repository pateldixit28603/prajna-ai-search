# Changelog

All notable changes to Prajna. Daily digest/benchmark commits from `prajna-bot` are not listed here.

## 2026-11-25
- Citations: a stricter prompt, plus conservative citation repair. An uncited sentence gets `[n]` only when at least 50% of its content words appear in source n's passages. The UI receives the repaired text through a `replace` SSE event. Validity and faithfulness are now averaged only over answers that have citations.
- Turned off Nemotron 3.5 "thinking" for answers (`LLM_EXTRA_BODY`). The probe in `scripts/llm_probe.py` showed reasoning tokens were using up the budget before the model wrote an answer, and that direct answers were about 7x faster. Also skips usage-only stream chunks. Reports now show how many answers the LLM actually wrote.
- Moved to NVIDIA's current Nemotron 3.5 family: Lightning 30B-A3B for answers, Bolt E4B for planning, Embed 1B and Rerank 8B. The previous hosted models reached end of life.
- Added `scripts/nim_check.py`, a daily NVIDIA endpoint health check with live-catalog discovery, and a circuit breaker for retired endpoints. Reports now say "NVIDIA NIM" only when the LLM actually wrote the answer.
- Added a benchmark harness (`backend/eval`) covering answer accuracy, retrieval recall, citation coverage and validity, lexical faithfulness and latency. It runs daily and writes [EVAL.md](EVAL.md) plus a history CSV.
- Added **Prajna Daily** (`backend/scripts/daily_digest.py`). It answers the day's trending Wikipedia and Hacker News topics with citations, then publishes [DIGEST.md](DIGEST.md) and a static site.
- Added GitHub Actions: CI (backend tests and frontend build) and a daily job that runs the digest and benchmark, commits the results and deploys to Pages.
- First release: FastAPI answer engine on NVIDIA NIM (Nemotron LLM, NeMo Retriever embeddings and reranker), with open-data sources (Wikipedia, OpenAlex, arXiv, Hacker News), a local hybrid index and a React UI.
