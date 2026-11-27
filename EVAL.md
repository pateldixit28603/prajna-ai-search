# Prajna benchmark

_Last run: 2026-11-27 01:22 UTC · mode: **NVIDIA NIM (24/24 answers by the LLM)** · 24 questions · runs automatically every day via GitHub Actions._

| Metric | Score | What it measures |
|---|---|---|
| Answer accuracy | **100%** | expected facts appear in the answer |
| Retrieval recall | **100%** | expected facts appear in retrieved sources |
| Citation coverage | **89%** | answer sentences carrying a [n] citation |
| Citation validity | **100%** | citations that point at a real source |
| Faithfulness (lexical) | **90%** | cited sentences supported by the cited passages |
| Latency p50 / p95 | **6.0s / 10.7s** | end-to-end, incl. live API calls |

## Per question

| id | focus | answer | sources | cites | faithful | sources used | time |
|---|---|---|---|---|---|---|---|
| nvidia-founded | wiki | ✅ | ✅ | 100% | 100% | 7 | 3.1s |
| cuda | wiki | ✅ | ✅ | 100% | 100% | 8 | 4.7s |
| transformer-paper | all | ✅ | ✅ | 100% | 100% | 8 | 2.9s |
| rag | all | ✅ | ✅ | 100% | 100% | 8 | 6.6s |
| bm25 | wiki | ✅ | ✅ | 80% | 100% | 4 | 5.8s |
| everest | wiki | ✅ | ✅ | 100% | 100% | 6 | 3.7s |
| photosynthesis | wiki | ✅ | ✅ | 83% | 100% | 8 | 4.7s |
| gita-chapters | wiki | ✅ | ✅ | 33% | 100% | 6 | 7.3s |
| taj-mahal | wiki | ✅ | ✅ | 100% | 100% | 8 | 6.0s |
| isro-chandrayaan3 | wiki | ✅ | ✅ | 100% | 100% | 6 | 8.3s |
| hinglish-cuda | wiki | ✅ | ✅ | 67% | 50% | 8 | 5.9s |
| hindi-gandhi | wiki | ✅ | ✅ | 100% | 100% | 8 | 6.5s |
| llm-hallucination | academic | ✅ | ✅ | 100% | 100% | 8 | 14.5s |
| small-lms | academic | ✅ | ✅ | 89% | 76% | 8 | 10.7s |
| vector-db | all | ✅ | ✅ | 100% | 100% | 8 | 7.7s |
| dense-retrieval | academic | ✅ | ✅ | 100% | 100% | 8 | 7.1s |
| hn-rust | tech | ✅ | ✅ | 100% | 100% | 6 | 8.9s |
| hn-local-llm | tech | ✅ | ✅ | 80% | 100% | 8 | 9.3s |
| tcp-udp | wiki | ✅ | ✅ | 100% | 75% | 8 | 4.9s |
| inflation | wiki | ✅ | ✅ | 100% | 100% | 8 | 9.9s |
| ru-nvidia | wiki | ✅ | ✅ | 100% | 50% | 8 | 5.1s |
| es-moon | wiki | ✅ | ✅ | 100% | 25% | 8 | 4.4s |
| zh-nvidia | wiki | ✅ | ✅ | 0% | – | 8 | 3.9s |
| ar-moon | wiki | ✅ | ✅ | 100% | 100% | 8 | 5.1s |

History: [`backend/eval/results/history.csv`](backend/eval/results/history.csv). Questions: [`backend/eval/questions.jsonl`](backend/eval/questions.jsonl).
