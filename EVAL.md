# Prajna benchmark

_Last run: 2026-11-25 17:26 UTC · mode: **NVIDIA NIM** · 20 questions · runs automatically every day via GitHub Actions._

| Metric | Score | What it measures |
|---|---|---|
| Answer accuracy | **80%** | expected facts appear in the answer |
| Retrieval recall | **100%** | expected facts appear in retrieved sources |
| Citation coverage | **81%** | answer sentences carrying a [n] citation |
| Citation validity | **90%** | citations that point at a real source |
| Faithfulness (lexical) | **87%** | cited sentences supported by the cited passages |
| Latency p50 / p95 | **12.3s / 39.5s** | end-to-end, incl. live API calls |

## Per question

| id | focus | answer | sources | cites | faithful | sources used | time |
|---|---|---|---|---|---|---|---|
| nvidia-founded | wiki | ✅ | ✅ | 100% | 100% | 8 | 11.7s |
| cuda | wiki | ✅ | ✅ | 100% | 100% | 8 | 13.0s |
| transformer-paper | all | ❌ | ✅ | 0% | 0% | 8 | 43.6s |
| rag | all | ✅ | ✅ | 100% | 100% | 8 | 11.9s |
| bm25 | wiki | ✅ | ✅ | 33% | 100% | 4 | 11.0s |
| everest | wiki | ✅ | ✅ | 100% | 100% | 6 | 10.1s |
| photosynthesis | wiki | ❌ | ✅ | 40% | 100% | 8 | 12.4s |
| gita-chapters | wiki | ❌ | ✅ | 100% | 100% | 6 | 12.3s |
| taj-mahal | wiki | ✅ | ✅ | 100% | 100% | 8 | 14.9s |
| isro-chandrayaan3 | wiki | ✅ | ✅ | 100% | 88% | 6 | 8.9s |
| hinglish-cuda | wiki | ✅ | ✅ | 100% | 100% | 8 | 13.3s |
| hindi-gandhi | wiki | ❌ | ✅ | 0% | 0% | 6 | 20.0s |
| llm-hallucination | academic | ✅ | ✅ | 100% | 100% | 8 | 15.7s |
| small-lms | academic | ✅ | ✅ | 100% | 100% | 8 | 13.3s |
| vector-db | all | ✅ | ✅ | 50% | 100% | 8 | 11.0s |
| dense-retrieval | academic | ✅ | ✅ | 100% | 100% | 8 | 11.0s |
| hn-rust | tech | ✅ | ✅ | 100% | 100% | 6 | 10.1s |
| hn-local-llm | tech | ✅ | ✅ | 100% | 100% | 8 | 39.5s |
| tcp-udp | wiki | ✅ | ✅ | 100% | 100% | 8 | 13.9s |
| inflation | wiki | ✅ | ✅ | 89% | 50% | 7 | 9.5s |

History: [`backend/eval/results/history.csv`](backend/eval/results/history.csv). Questions: [`backend/eval/questions.jsonl`](backend/eval/questions.jsonl).
