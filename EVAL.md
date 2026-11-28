# Prajna benchmark

_Last run: 2026-11-28 00:55 UTC · mode: **NVIDIA NIM (24/24 answers by the LLM)** · 24 questions · runs automatically every day via GitHub Actions._

| Metric | Score | What it measures |
|---|---|---|
| Answer accuracy | **100%** | expected facts appear in the answer |
| Retrieval recall | **100%** | expected facts appear in retrieved sources |
| Citation coverage | **95%** | answer sentences carrying a [n] citation |
| Citation validity | **100%** | citations that point at a real source |
| Faithfulness (lexical) | **83%** | cited sentences supported by the cited passages |
| Latency p50 / p95 | **2.9s / 5.2s** | end-to-end, incl. live API calls |

## Per question

| id | focus | answer | sources | cites | faithful | sources used | time |
|---|---|---|---|---|---|---|---|
| nvidia-founded | wiki | ✅ | ✅ | 100% | 100% | 8 | 2.4s |
| cuda | wiki | ✅ | ✅ | 100% | 100% | 8 | 2.7s |
| transformer-paper | all | ✅ | ✅ | 100% | 100% | 8 | 2.4s |
| rag | all | ✅ | ✅ | 100% | 100% | 8 | 4.0s |
| bm25 | wiki | ✅ | ✅ | 80% | 75% | 4 | 2.4s |
| everest | wiki | ✅ | ✅ | 100% | 100% | 6 | 1.9s |
| photosynthesis | wiki | ✅ | ✅ | 100% | 100% | 6 | 4.0s |
| gita-chapters | wiki | ✅ | ✅ | 67% | 100% | 6 | 2.2s |
| taj-mahal | wiki | ✅ | ✅ | 83% | 100% | 8 | 3.2s |
| isro-chandrayaan3 | wiki | ✅ | ✅ | 100% | 100% | 6 | 3.6s |
| hinglish-cuda | wiki | ✅ | ✅ | 69% | 22% | 8 | 5.7s |
| hindi-gandhi | wiki | ✅ | ✅ | 100% | 100% | 8 | 2.7s |
| llm-hallucination | academic | ✅ | ✅ | 100% | 100% | 8 | 4.9s |
| small-lms | academic | ✅ | ✅ | 89% | 100% | 8 | 5.0s |
| vector-db | all | ✅ | ✅ | 100% | 100% | 8 | 4.6s |
| dense-retrieval | academic | ✅ | ✅ | 100% | 100% | 8 | 5.2s |
| hn-rust | tech | ✅ | ✅ | 100% | 67% | 4 | 2.7s |
| hn-local-llm | tech | ✅ | ✅ | 100% | 67% | 8 | 3.5s |
| tcp-udp | wiki | ✅ | ✅ | 80% | 50% | 8 | 3.0s |
| inflation | wiki | ✅ | ✅ | 100% | 100% | 8 | 2.4s |
| ru-nvidia | wiki | ✅ | ✅ | 100% | 50% | 8 | 2.0s |
| es-moon | wiki | ✅ | ✅ | 100% | 50% | 8 | 2.2s |
| zh-nvidia | wiki | ✅ | ✅ | 100% | 0% | 8 | 2.7s |
| ar-moon | wiki | ✅ | ✅ | 100% | 100% | 8 | 3.1s |

History: [`backend/eval/results/history.csv`](backend/eval/results/history.csv). Questions: [`backend/eval/questions.jsonl`](backend/eval/questions.jsonl).
