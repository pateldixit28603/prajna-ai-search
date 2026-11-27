# Prajna benchmark

_Last run: 2026-11-27 20:04 UTC · mode: **NVIDIA NIM (24/24 answers by the LLM)** · 24 questions · runs automatically every day via GitHub Actions._

| Metric | Score | What it measures |
|---|---|---|
| Answer accuracy | **100%** | expected facts appear in the answer |
| Retrieval recall | **100%** | expected facts appear in retrieved sources |
| Citation coverage | **91%** | answer sentences carrying a [n] citation |
| Citation validity | **100%** | citations that point at a real source |
| Faithfulness (lexical) | **83%** | cited sentences supported by the cited passages |
| Latency p50 / p95 | **7.9s / 18.1s** | end-to-end, incl. live API calls |

## Per question

| id | focus | answer | sources | cites | faithful | sources used | time |
|---|---|---|---|---|---|---|---|
| nvidia-founded | wiki | ✅ | ✅ | 100% | 100% | 8 | 2.5s |
| cuda | wiki | ✅ | ✅ | 100% | 100% | 8 | 6.5s |
| transformer-paper | all | ✅ | ✅ | 100% | 100% | 8 | 7.9s |
| rag | all | ✅ | ✅ | 100% | 100% | 8 | 13.7s |
| bm25 | wiki | ✅ | ✅ | 80% | 100% | 4 | 3.2s |
| everest | wiki | ✅ | ✅ | 100% | 100% | 6 | 7.9s |
| photosynthesis | wiki | ✅ | ✅ | 100% | 83% | 6 | 8.4s |
| gita-chapters | wiki | ✅ | ✅ | 25% | 100% | 6 | 6.5s |
| taj-mahal | wiki | ✅ | ✅ | 86% | 100% | 8 | 6.5s |
| isro-chandrayaan3 | wiki | ✅ | ✅ | 100% | 100% | 6 | 9.3s |
| hinglish-cuda | wiki | ✅ | ✅ | 38% | 50% | 8 | 9.5s |
| hindi-gandhi | wiki | ✅ | ✅ | 100% | 100% | 8 | 7.6s |
| llm-hallucination | academic | ✅ | ✅ | 88% | 100% | 8 | 9.3s |
| small-lms | academic | ✅ | ✅ | 100% | 100% | 8 | 18.1s |
| vector-db | all | ✅ | ✅ | 91% | 100% | 8 | 10.7s |
| dense-retrieval | academic | ✅ | ✅ | 100% | 100% | 8 | 9.1s |
| hn-rust | tech | ✅ | ✅ | 100% | 100% | 3 | 5.8s |
| hn-local-llm | tech | ✅ | ✅ | 85% | 100% | 8 | 5.4s |
| tcp-udp | wiki | ✅ | ✅ | 100% | 50% | 8 | 5.8s |
| inflation | wiki | ✅ | ✅ | 100% | 92% | 8 | 9.4s |
| ru-nvidia | wiki | ✅ | ✅ | 100% | 75% | 8 | 5.8s |
| es-moon | wiki | ✅ | ✅ | 100% | 50% | 8 | 9.3s |
| zh-nvidia | wiki | ✅ | ✅ | 100% | 0% | 8 | 6.6s |
| ar-moon | wiki | ✅ | ✅ | 100% | 0% | 6 | 20.6s |

History: [`backend/eval/results/history.csv`](backend/eval/results/history.csv). Questions: [`backend/eval/questions.jsonl`](backend/eval/questions.jsonl).
