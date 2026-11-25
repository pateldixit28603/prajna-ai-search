# Prajna benchmark

_Last run: 2026-11-25 17:06 UTC · mode: **NVIDIA NIM** · 20 questions · runs automatically every day via GitHub Actions._

| Metric | Score | What it measures |
|---|---|---|
| Answer accuracy | **70%** | expected facts appear in the answer |
| Retrieval recall | **90%** | expected facts appear in retrieved sources |
| Citation coverage | **95%** | answer sentences carrying a [n] citation |
| Citation validity | **95%** | citations that point at a real source |
| Faithfulness (lexical) | **95%** | cited sentences supported by the cited passages |
| Latency p50 / p95 | **0.6s / 2.5s** | end-to-end, incl. live API calls |

## Per question

| id | focus | answer | sources | cites | faithful | sources used | time |
|---|---|---|---|---|---|---|---|
| nvidia-founded | wiki | ✅ | ✅ | 100% | 100% | 6 | 0.6s |
| cuda | wiki | ✅ | ✅ | 100% | 100% | 5 | 0.3s |
| transformer-paper | all | ❌ | ✅ | 100% | 100% | 8 | 0.7s |
| rag | all | ✅ | ✅ | 100% | 100% | 8 | 0.7s |
| bm25 | wiki | ✅ | ✅ | 100% | 100% | 2 | 0.3s |
| everest | wiki | ❌ | ✅ | 100% | 100% | 6 | 0.9s |
| photosynthesis | wiki | ✅ | ✅ | 100% | 100% | 6 | 2.5s |
| gita-chapters | wiki | ❌ | ✅ | 100% | 100% | 6 | 0.4s |
| taj-mahal | wiki | ❌ | ✅ | 100% | 100% | 6 | 1.4s |
| isro-chandrayaan3 | wiki | ✅ | ✅ | 100% | 100% | 6 | 8.1s |
| hinglish-cuda | wiki | ❌ | ❌ | 0% | 0% | 0 | 0.2s |
| hindi-gandhi | wiki | ❌ | ❌ | 100% | 100% | 6 | 0.7s |
| llm-hallucination | academic | ✅ | ✅ | 100% | 100% | 8 | 0.9s |
| small-lms | academic | ✅ | ✅ | 100% | 100% | 8 | 0.6s |
| vector-db | all | ✅ | ✅ | 100% | 100% | 8 | 0.7s |
| dense-retrieval | academic | ✅ | ✅ | 100% | 100% | 6 | 0.6s |
| hn-rust | tech | ✅ | ✅ | 100% | 100% | 1 | 0.4s |
| hn-local-llm | tech | ✅ | ✅ | 100% | 100% | 8 | 0.4s |
| tcp-udp | wiki | ✅ | ✅ | 100% | 100% | 6 | 0.5s |
| inflation | wiki | ✅ | ✅ | 100% | 100% | 6 | 1.1s |

History: [`backend/eval/results/history.csv`](backend/eval/results/history.csv). Questions: [`backend/eval/questions.jsonl`](backend/eval/questions.jsonl).
