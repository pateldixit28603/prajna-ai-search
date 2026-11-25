# Prajna benchmark

_Last run: 2026-11-25 17:10 UTC · mode: **extractive (no NVIDIA key)** · 20 questions · runs automatically every day via GitHub Actions._

| Metric | Score | What it measures |
|---|---|---|
| Answer accuracy | **70%** | expected facts appear in the answer |
| Retrieval recall | **90%** | expected facts appear in retrieved sources |
| Citation coverage | **95%** | answer sentences carrying a [n] citation |
| Citation validity | **95%** | citations that point at a real source |
| Faithfulness (lexical) | **95%** | cited sentences supported by the cited passages |
| Latency p50 / p95 | **0.6s / 1.2s** | end-to-end, incl. live API calls |

## Per question

| id | focus | answer | sources | cites | faithful | sources used | time |
|---|---|---|---|---|---|---|---|
| nvidia-founded | wiki | ✅ | ✅ | 100% | 100% | 6 | 0.6s |
| cuda | wiki | ✅ | ✅ | 100% | 100% | 5 | 0.3s |
| transformer-paper | all | ❌ | ✅ | 100% | 100% | 8 | 0.9s |
| rag | all | ✅ | ✅ | 100% | 100% | 8 | 0.9s |
| bm25 | wiki | ✅ | ✅ | 100% | 100% | 2 | 0.4s |
| everest | wiki | ❌ | ✅ | 100% | 100% | 6 | 0.4s |
| photosynthesis | wiki | ✅ | ✅ | 100% | 100% | 6 | 0.4s |
| gita-chapters | wiki | ❌ | ✅ | 100% | 100% | 6 | 0.5s |
| taj-mahal | wiki | ❌ | ✅ | 100% | 100% | 6 | 0.4s |
| isro-chandrayaan3 | wiki | ✅ | ✅ | 100% | 100% | 6 | 0.4s |
| hinglish-cuda | wiki | ❌ | ❌ | 0% | 0% | 0 | 0.2s |
| hindi-gandhi | wiki | ❌ | ❌ | 100% | 100% | 6 | 0.7s |
| llm-hallucination | academic | ✅ | ✅ | 100% | 100% | 8 | 0.6s |
| small-lms | academic | ✅ | ✅ | 100% | 100% | 8 | 1.0s |
| vector-db | all | ✅ | ✅ | 100% | 100% | 8 | 1.1s |
| dense-retrieval | academic | ✅ | ✅ | 100% | 100% | 6 | 0.6s |
| hn-rust | tech | ✅ | ✅ | 100% | 100% | 1 | 2.2s |
| hn-local-llm | tech | ✅ | ✅ | 100% | 100% | 8 | 1.2s |
| tcp-udp | wiki | ✅ | ✅ | 100% | 100% | 6 | 0.4s |
| inflation | wiki | ✅ | ✅ | 100% | 100% | 6 | 0.4s |

History: [`backend/eval/results/history.csv`](backend/eval/results/history.csv). Questions: [`backend/eval/questions.jsonl`](backend/eval/questions.jsonl).
