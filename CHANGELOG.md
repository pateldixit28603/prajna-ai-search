# Changelog

All notable changes to Prajna. Daily digest/benchmark commits from `prajna-bot` are not listed here.

## 2026-11-25
- Added a benchmark harness (`backend/eval`) covering answer accuracy, retrieval recall, citation coverage and validity, lexical faithfulness and latency. It runs daily and writes [EVAL.md](EVAL.md) plus a history CSV.
- Added **Prajna Daily** (`backend/scripts/daily_digest.py`). It answers the day's trending Wikipedia and Hacker News topics with citations, then publishes [DIGEST.md](DIGEST.md) and a static site.
- Added GitHub Actions: CI (backend tests and frontend build) and a daily job that runs the digest and benchmark, commits the results and deploys to Pages.
- First release: FastAPI answer engine on NVIDIA NIM (Nemotron LLM, NeMo Retriever embeddings and reranker), with open-data sources (Wikipedia, OpenAlex, arXiv, Hacker News), a local hybrid index and a React UI.
