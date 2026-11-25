# Prajna benchmark

_Last run: 2026-11-25 16:54 UTC · mode: **extractive (no NVIDIA key)** · 20 questions · runs automatically every day via GitHub Actions._

| Metric | Score | What it measures |
|---|---|---|
| Answer accuracy | **70%** | expected facts appear in the answer |
| Retrieval recall | **90%** | expected facts appear in retrieved sources |
| Citation coverage | **95%** | answer sentences carrying a [n] citation |
| Citation validity | **95%** | citations that point at a real source |
| Faithfulness (lexical) | **95%** | cited sentences supported by the cited passages |
| Latency p50 / p95 | **1.1s / 1.4s** | end-to-end, incl. live API calls |

## Per question

| id | focus | answer | sources | cites | faithful | sources used | time |
|---|---|---|---|---|---|---|---|
| nvidia-founded | wiki | ✅ | ✅ | 100% | 100% | 6 | 1.1s |
| cuda | wiki | ✅ | ✅ | 100% | 100% | 5 | 0.9s |
| transformer-paper | all | ❌ | ✅ | 100% | 100% | 8 | 1.5s |
| rag | all | ✅ | ✅ | 100% | 100% | 8 | 1.1s |
| bm25 | wiki | ✅ | ✅ | 100% | 100% | 2 | 0.8s |
| everest | wiki | ❌ | ✅ | 100% | 100% | 6 | 1.1s |
| photosynthesis | wiki | ✅ | ✅ | 100% | 100% | 6 | 0.9s |
| gita-chapters | wiki | ❌ | ✅ | 100% | 100% | 6 | 1.4s |
| taj-mahal | wiki | ❌ | ✅ | 100% | 100% | 6 | 1.3s |
| isro-chandrayaan3 | wiki | ✅ | ✅ | 100% | 100% | 6 | 1.4s |
| hinglish-cuda | wiki | ❌ | ❌ | 0% | 0% | 0 | 0.2s |
| hindi-gandhi | wiki | ❌ | ❌ | 100% | 100% | 6 | 1.2s |
| llm-hallucination | academic | ✅ | ✅ | 100% | 100% | 8 | 0.9s |
| small-lms | academic | ✅ | ✅ | 100% | 100% | 8 | 0.9s |
| vector-db | all | ✅ | ✅ | 100% | 100% | 8 | 1.1s |
| dense-retrieval | academic | ✅ | ✅ | 100% | 100% | 6 | 0.7s |
| hn-rust | tech | ✅ | ✅ | 100% | 100% | 1 | 0.9s |
| hn-local-llm | tech | ✅ | ✅ | 100% | 100% | 8 | 1.1s |
| tcp-udp | wiki | ✅ | ✅ | 100% | 100% | 6 | 1.2s |
| inflation | wiki | ✅ | ✅ | 100% | 100% | 6 | 1.1s |

History: [`backend/eval/results/history.csv`](backend/eval/results/history.csv). Questions: [`backend/eval/questions.jsonl`](backend/eval/questions.jsonl).
