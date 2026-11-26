# Changelog

All notable changes to Prajna. Daily digest/benchmark commits from `prajna-bot` are not listed here.

## 2026-11-26
- **Create images.** A new **Create image** mode in the search box generates pictures with NVIDIA visual GenAI. FLUX.1 schnell is tried first, then FLUX.1 dev, FLUX.2 klein and Stable Diffusion 3 Medium; a model that is retired or not enabled on the account is skipped. Nemotron Bolt first expands a short idea (in any language) into a detailed prompt and shows it. Choose square, wide or tall. Images can be downloaded, re-rolled with **Variation**, and are saved in your history. If NVIDIA's safety filter blocks a prompt, or no model answers, you get a plain message instead of a broken image.
- **Research mode.** Every answer has a new **Research** tab that maps the scholarly literature on the topic from OpenAlex: key papers, the most-cited foundational works, what's rising in the last two years, a "read next" list of works related to several key papers, and a publications-per-year timeline that shows when the field took off. Each paper shows its citation count, venue, authors and a free full-text link when one exists.
- The daily NVIDIA health check now also test-renders one image and runs one research lookup, so `nim_status.json` shows whether both work.
- **Answer in 7 languages.** Every answer now has a one-click language switch: English, 简体中文, हिन्दी, Español, العربية, Русский and Hinglish. The NVIDIA NIM LLM re-renders the answer without searching again. Prajna then checks the citations: any `[n]` the translation dropped is put back on the same paragraph, and invented numbers are removed, so each citation still points at the same source. Arabic answers display right-to-left. Translations are cached on the thread, so switching back is instant.
- Pick the answer language before you search, or leave it on **Auto**, which detects it from the question's script (Devanagari → Hindi, Cyrillic → Russian, Arabic script → Arabic, Chinese characters → Chinese, plus word lists for Hinglish and Spanish). The choice is saved with the thread, and follow-ups inherit it.
- Non-English questions also search the matching Wikipedia edition (ru, zh, hi, es, ar.wikipedia.org) alongside the English sources.
- If NVIDIA is unavailable, the switch keeps the original answer and says why.
- Benchmark: added Russian, Spanish, Chinese and Arabic questions (24 questions in total), so scores from this date onward aren't directly comparable with earlier runs.

## 2026-11-25
- Added one-click Render deploy (`render.yaml`). The Dockerfile now honours `$PORT`, and CI builds the image and smoke-tests the UI and API in a container.
- Citations: a stricter prompt, plus conservative citation repair. An uncited sentence gets `[n]` only when at least 50% of its content words appear in source n's passages. The UI receives the repaired text through a `replace` SSE event. Validity and faithfulness are now averaged only over answers that have citations.
- Turned off Nemotron 3.5 "thinking" for answers (`LLM_EXTRA_BODY`). The probe in `scripts/llm_probe.py` showed reasoning tokens were using up the budget before the model wrote an answer, and that direct answers were about 7x faster. Also skips usage-only stream chunks. Reports now show how many answers the LLM actually wrote.
- Moved to NVIDIA's current Nemotron 3.5 family: Lightning 30B-A3B for answers, Bolt E4B for planning, Embed 1B and Rerank 8B. The previous hosted models reached end of life.
- Added `scripts/nim_check.py`, a daily NVIDIA endpoint health check with live-catalog discovery, and a circuit breaker for retired endpoints. Reports now say "NVIDIA NIM" only when the LLM actually wrote the answer.
- Added a benchmark harness (`backend/eval`) covering answer accuracy, retrieval recall, citation coverage and validity, lexical faithfulness and latency. It runs daily and writes [EVAL.md](EVAL.md) plus a history CSV.
- Added **Prajna Daily** (`backend/scripts/daily_digest.py`). It answers the day's trending Wikipedia and Hacker News topics with citations, then publishes [DIGEST.md](DIGEST.md) and a static site.
- Added GitHub Actions: CI (backend tests and frontend build) and a daily job that runs the digest and benchmark, commits the results and deploys to Pages.
- First release: FastAPI answer engine on NVIDIA NIM (Nemotron LLM, NeMo Retriever embeddings and reranker), with open-data sources (Wikipedia, OpenAlex, arXiv, Hacker News), a local hybrid index and a React UI.
