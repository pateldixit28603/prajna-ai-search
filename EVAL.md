# Prajna benchmark

_Last run: 2026-11-25 17:18 UTC · mode: **NVIDIA NIM** · 20 questions · runs automatically every day via GitHub Actions._

| Metric | Score | What it measures |
|---|---|---|
| Answer accuracy | **95%** | expected facts appear in the answer |
| Retrieval recall | **100%** | expected facts appear in retrieved sources |
| Citation coverage | **93%** | answer sentences carrying a [n] citation |
| Citation validity | **100%** | citations that point at a real source |
| Faithfulness (lexical) | **95%** | cited sentences supported by the cited passages |
| Latency p50 / p95 | **11.5s / 18.3s** | end-to-end, incl. live API calls |

## Per question

| id | focus | answer | sources | cites | faithful | sources used | time |
|---|---|---|---|---|---|---|---|
| nvidia-founded | wiki | ✅ | ✅ | 100% | 100% | 8 | 8.4s |
| cuda | wiki | ✅ | ✅ | 38% | 100% | 5 | 12.6s |
| transformer-paper | all | ✅ | ✅ | 75% | 100% | 8 | 9.5s |
| rag | all | ✅ | ✅ | 100% | 100% | 8 | 12.2s |
| bm25 | wiki | ✅ | ✅ | 100% | 100% | 4 | 11.7s |
| everest | wiki | ✅ | ✅ | 100% | 100% | 6 | 15.0s |
| photosynthesis | wiki | ✅ | ✅ | 100% | 100% | 8 | 8.5s |
| gita-chapters | wiki | ❌ | ✅ | 71% | 100% | 6 | 10.9s |
| taj-mahal | wiki | ✅ | ✅ | 100% | 100% | 8 | 10.7s |
| isro-chandrayaan3 | wiki | ✅ | ✅ | 67% | 100% | 6 | 14.2s |
| hinglish-cuda | wiki | ✅ | ✅ | 100% | 100% | 8 | 20.5s |
| hindi-gandhi | wiki | ✅ | ✅ | 100% | 0% | 6 | 17.0s |
| llm-hallucination | academic | ✅ | ✅ | 100% | 100% | 8 | 10.8s |
| small-lms | academic | ✅ | ✅ | 100% | 100% | 8 | 9.9s |
| vector-db | all | ✅ | ✅ | 100% | 100% | 8 | 18.3s |
| dense-retrieval | academic | ✅ | ✅ | 100% | 100% | 8 | 11.4s |
| hn-rust | tech | ✅ | ✅ | 100% | 100% | 6 | 13.3s |
| hn-local-llm | tech | ✅ | ✅ | 100% | 100% | 8 | 12.4s |
| tcp-udp | wiki | ✅ | ✅ | 100% | 100% | 8 | 8.9s |
| inflation | wiki | ✅ | ✅ | 100% | 100% | 8 | 10.9s |

History: [`backend/eval/results/history.csv`](backend/eval/results/history.csv). Questions: [`backend/eval/questions.jsonl`](backend/eval/questions.jsonl).
