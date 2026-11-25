# Prajna benchmark

_Last run: 2026-11-25 17:08 UTC · mode: **extractive (no NVIDIA key)** · 20 questions · runs automatically every day via GitHub Actions._

| Metric | Score | What it measures |
|---|---|---|
| Answer accuracy | **65%** | expected facts appear in the answer |
| Retrieval recall | **85%** | expected facts appear in retrieved sources |
| Citation coverage | **85%** | answer sentences carrying a [n] citation |
| Citation validity | **85%** | citations that point at a real source |
| Faithfulness (lexical) | **85%** | cited sentences supported by the cited passages |
| Latency p50 / p95 | **0.7s / 1.5s** | end-to-end, incl. live API calls |

## Per question

| id | focus | answer | sources | cites | faithful | sources used | time |
|---|---|---|---|---|---|---|---|
| nvidia-founded | wiki | ✅ | ✅ | 100% | 100% | 6 | 1.5s |
| cuda | wiki | ✅ | ✅ | 100% | 100% | 5 | 0.5s |
| transformer-paper | all | ❌ | ✅ | 100% | 100% | 8 | 0.8s |
| rag | all | ✅ | ✅ | 100% | 100% | 8 | 0.7s |
| bm25 | wiki | ✅ | ✅ | 100% | 100% | 2 | 0.5s |
| everest | wiki | ❌ | ✅ | 100% | 100% | 6 | 0.5s |
| photosynthesis | wiki | ❌ | ❌ | 0% | 0% | 0 | 12.2s |
| gita-chapters | wiki | ❌ | ✅ | 100% | 100% | 6 | 0.7s |
| taj-mahal | wiki | ❌ | ✅ | 100% | 100% | 6 | 0.7s |
| isro-chandrayaan3 | wiki | ✅ | ✅ | 100% | 100% | 6 | 0.5s |
| hinglish-cuda | wiki | ❌ | ❌ | 0% | 0% | 0 | 0.2s |
| hindi-gandhi | wiki | ❌ | ❌ | 0% | 0% | 0 | 0.5s |
| llm-hallucination | academic | ✅ | ✅ | 100% | 100% | 8 | 0.9s |
| small-lms | academic | ✅ | ✅ | 100% | 100% | 8 | 0.8s |
| vector-db | all | ✅ | ✅ | 100% | 100% | 8 | 0.9s |
| dense-retrieval | academic | ✅ | ✅ | 100% | 100% | 6 | 0.6s |
| hn-rust | tech | ✅ | ✅ | 100% | 100% | 1 | 0.5s |
| hn-local-llm | tech | ✅ | ✅ | 100% | 100% | 8 | 0.8s |
| tcp-udp | wiki | ✅ | ✅ | 100% | 100% | 6 | 1.0s |
| inflation | wiki | ✅ | ✅ | 100% | 100% | 6 | 0.5s |

History: [`backend/eval/results/history.csv`](backend/eval/results/history.csv). Questions: [`backend/eval/questions.jsonl`](backend/eval/questions.jsonl).
