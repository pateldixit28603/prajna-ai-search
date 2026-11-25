# Prajna benchmark

_Last run: 2026-11-25 17:37 UTC · mode: **NVIDIA NIM (20/20 answers by the LLM)** · 20 questions · runs automatically every day via GitHub Actions._

| Metric | Score | What it measures |
|---|---|---|
| Answer accuracy | **100%** | expected facts appear in the answer |
| Retrieval recall | **100%** | expected facts appear in retrieved sources |
| Citation coverage | **94%** | answer sentences carrying a [n] citation |
| Citation validity | **100%** | citations that point at a real source |
| Faithfulness (lexical) | **80%** | cited sentences supported by the cited passages |
| Latency p50 / p95 | **4.2s / 7.7s** | end-to-end, incl. live API calls |

## Per question

| id | focus | answer | sources | cites | faithful | sources used | time |
|---|---|---|---|---|---|---|---|
| nvidia-founded | wiki | ✅ | ✅ | 100% | 100% | 8 | 3.8s |
| cuda | wiki | ✅ | ✅ | 100% | 100% | 8 | 5.7s |
| transformer-paper | all | ✅ | ✅ | 100% | 75% | 8 | 4.0s |
| rag | all | ✅ | ✅ | 100% | 100% | 8 | 4.1s |
| bm25 | wiki | ✅ | ✅ | 100% | 80% | 4 | 3.9s |
| everest | wiki | ✅ | ✅ | 100% | 100% | 6 | 3.2s |
| photosynthesis | wiki | ✅ | ✅ | 89% | 50% | 8 | 4.3s |
| gita-chapters | wiki | ✅ | ✅ | 100% | 67% | 6 | 2.5s |
| taj-mahal | wiki | ✅ | ✅ | 100% | 100% | 8 | 5.0s |
| isro-chandrayaan3 | wiki | ✅ | ✅ | 100% | 100% | 6 | 3.7s |
| hinglish-cuda | wiki | ✅ | ✅ | 29% | 0% | 8 | 7.4s |
| hindi-gandhi | wiki | ✅ | ✅ | 100% | 0% | 6 | 3.6s |
| llm-hallucination | academic | ✅ | ✅ | 100% | 100% | 8 | 7.7s |
| small-lms | academic | ✅ | ✅ | 100% | 73% | 8 | 8.7s |
| vector-db | all | ✅ | ✅ | 100% | 78% | 8 | 4.8s |
| dense-retrieval | academic | ✅ | ✅ | 100% | 100% | 8 | 4.6s |
| hn-rust | tech | ✅ | ✅ | 100% | 75% | 6 | 2.9s |
| hn-local-llm | tech | ✅ | ✅ | 78% | 100% | 8 | 5.4s |
| tcp-udp | wiki | ✅ | ✅ | 100% | 100% | 8 | 2.7s |
| inflation | wiki | ✅ | ✅ | 89% | 100% | 7 | 5.2s |

History: [`backend/eval/results/history.csv`](backend/eval/results/history.csv). Questions: [`backend/eval/questions.jsonl`](backend/eval/questions.jsonl).
