# Prajna benchmark

_Last run: 2026-11-28 19:08 UTC · mode: **NVIDIA NIM (24/24 answers by the LLM)** · 24 questions · runs automatically every day via GitHub Actions._

| Metric | Score | What it measures |
|---|---|---|
| Answer accuracy | **96%** | expected facts appear in the answer |
| Retrieval recall | **100%** | expected facts appear in retrieved sources |
| Citation coverage | **86%** | answer sentences carrying a [n] citation |
| Citation validity | **100%** | citations that point at a real source |
| Faithfulness (lexical) | **95%** | cited sentences supported by the cited passages |
| Latency p50 / p95 | **21.0s / 29.7s** | end-to-end, incl. live API calls |

## Per question

| id | focus | answer | sources | cites | faithful | sources used | time |
|---|---|---|---|---|---|---|---|
| nvidia-founded | wiki | ✅ | ✅ | 100% | 100% | 8 | 28.2s |
| cuda | wiki | ✅ | ✅ | 100% | 100% | 5 | 21.9s |
| transformer-paper | all | ✅ | ✅ | 100% | 100% | 8 | 11.7s |
| rag | all | ✅ | ✅ | 100% | 100% | 8 | 29.8s |
| bm25 | wiki | ✅ | ✅ | 80% | 100% | 4 | 21.9s |
| everest | wiki | ✅ | ✅ | 100% | 100% | 6 | 21.0s |
| photosynthesis | wiki | ❌ | ✅ | 80% | 100% | 6 | 16.6s |
| gita-chapters | wiki | ✅ | ✅ | 100% | 100% | 6 | 23.3s |
| taj-mahal | wiki | ✅ | ✅ | 83% | 100% | 8 | 29.4s |
| isro-chandrayaan3 | wiki | ✅ | ✅ | 100% | 100% | 6 | 20.4s |
| hinglish-cuda | wiki | ✅ | ✅ | 56% | 89% | 8 | 24.1s |
| hindi-gandhi | wiki | ✅ | ✅ | 100% | 100% | 8 | 12.3s |
| llm-hallucination | academic | ✅ | ✅ | 100% | 100% | 8 | 16.7s |
| small-lms | academic | ✅ | ✅ | 100% | 100% | 8 | 21.0s |
| vector-db | all | ✅ | ✅ | 90% | 78% | 8 | 13.1s |
| dense-retrieval | academic | ✅ | ✅ | 100% | 100% | 8 | 22.4s |
| hn-rust | tech | ✅ | ✅ | 88% | 86% | 3 | 22.9s |
| hn-local-llm | tech | ✅ | ✅ | 88% | 100% | 8 | 29.7s |
| tcp-udp | wiki | ✅ | ✅ | 100% | 83% | 8 | 23.5s |
| inflation | wiki | ✅ | ✅ | 100% | 100% | 8 | 14.5s |
| ru-nvidia | wiki | ✅ | ✅ | 100% | 100% | 8 | 6.8s |
| es-moon | wiki | ✅ | ✅ | 100% | 50% | 8 | 3.1s |
| zh-nvidia | wiki | ✅ | ✅ | 0% | – | 8 | 2.2s |
| ar-moon | wiki | ✅ | ✅ | 0% | – | 8 | 4.1s |

History: [`backend/eval/results/history.csv`](backend/eval/results/history.csv). Questions: [`backend/eval/questions.jsonl`](backend/eval/questions.jsonl).
