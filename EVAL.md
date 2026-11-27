# Prajna benchmark

_Last run: 2026-11-27 01:36 UTC · mode: **NVIDIA NIM (24/24 answers by the LLM)** · 24 questions · runs automatically every day via GitHub Actions._

| Metric | Score | What it measures |
|---|---|---|
| Answer accuracy | **100%** | expected facts appear in the answer |
| Retrieval recall | **100%** | expected facts appear in retrieved sources |
| Citation coverage | **92%** | answer sentences carrying a [n] citation |
| Citation validity | **100%** | citations that point at a real source |
| Faithfulness (lexical) | **91%** | cited sentences supported by the cited passages |
| Latency p50 / p95 | **7.5s / 12.6s** | end-to-end, incl. live API calls |

## Per question

| id | focus | answer | sources | cites | faithful | sources used | time |
|---|---|---|---|---|---|---|---|
| nvidia-founded | wiki | ✅ | ✅ | 100% | 100% | 7 | 2.7s |
| cuda | wiki | ✅ | ✅ | 100% | 100% | 8 | 8.2s |
| transformer-paper | all | ✅ | ✅ | 100% | 100% | 8 | 2.4s |
| rag | all | ✅ | ✅ | 100% | 100% | 8 | 8.0s |
| bm25 | wiki | ✅ | ✅ | 83% | 100% | 4 | 5.2s |
| everest | wiki | ✅ | ✅ | 100% | 100% | 6 | 5.7s |
| photosynthesis | wiki | ✅ | ✅ | 90% | 89% | 8 | 6.3s |
| gita-chapters | wiki | ✅ | ✅ | 100% | 100% | 6 | 3.3s |
| taj-mahal | wiki | ✅ | ✅ | 100% | 100% | 8 | 5.3s |
| isro-chandrayaan3 | wiki | ✅ | ✅ | 100% | 100% | 6 | 5.2s |
| hinglish-cuda | wiki | ✅ | ✅ | 41% | 43% | 8 | 12.8s |
| hindi-gandhi | wiki | ✅ | ✅ | 100% | 100% | 8 | 6.7s |
| llm-hallucination | academic | ✅ | ✅ | 100% | 100% | 8 | 7.4s |
| small-lms | academic | ✅ | ✅ | 100% | 100% | 8 | 6.3s |
| vector-db | all | ✅ | ✅ | 100% | 78% | 8 | 9.9s |
| dense-retrieval | academic | ✅ | ✅ | 100% | 100% | 8 | 8.4s |
| hn-rust | tech | ✅ | ✅ | 100% | 100% | 6 | 7.9s |
| hn-local-llm | tech | ✅ | ✅ | 83% | 100% | 8 | 12.6s |
| tcp-udp | wiki | ✅ | ✅ | 100% | 75% | 8 | 10.6s |
| inflation | wiki | ✅ | ✅ | 100% | 100% | 8 | 8.7s |
| ru-nvidia | wiki | ✅ | ✅ | 100% | 50% | 8 | 8.5s |
| es-moon | wiki | ✅ | ✅ | 100% | 50% | 8 | 9.1s |
| zh-nvidia | wiki | ✅ | ✅ | 0% | – | 8 | 6.0s |
| ar-moon | wiki | ✅ | ✅ | 100% | 100% | 8 | 7.6s |

History: [`backend/eval/results/history.csv`](backend/eval/results/history.csv). Questions: [`backend/eval/questions.jsonl`](backend/eval/questions.jsonl).
