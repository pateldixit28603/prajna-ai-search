# Prajna benchmark

_Last run: 2026-11-26 15:20 UTC · mode: **NVIDIA NIM (24/24 answers by the LLM)** · 24 questions · runs automatically every day via GitHub Actions._

| Metric | Score | What it measures |
|---|---|---|
| Answer accuracy | **100%** | expected facts appear in the answer |
| Retrieval recall | **100%** | expected facts appear in retrieved sources |
| Citation coverage | **85%** | answer sentences carrying a [n] citation |
| Citation validity | **100%** | citations that point at a real source |
| Faithfulness (lexical) | **91%** | cited sentences supported by the cited passages |
| Latency p50 / p95 | **4.6s / 13.2s** | end-to-end, incl. live API calls |

## Per question

| id | focus | answer | sources | cites | faithful | sources used | time |
|---|---|---|---|---|---|---|---|
| nvidia-founded | wiki | ✅ | ✅ | 100% | 100% | 7 | 3.8s |
| cuda | wiki | ✅ | ✅ | 100% | 100% | 8 | 13.2s |
| transformer-paper | all | ✅ | ✅ | 100% | 100% | 8 | 2.6s |
| rag | all | ✅ | ✅ | 100% | 100% | 8 | 4.6s |
| bm25 | wiki | ✅ | ✅ | 80% | 100% | 4 | 3.4s |
| everest | wiki | ✅ | ✅ | 100% | 100% | 6 | 3.7s |
| photosynthesis | wiki | ✅ | ✅ | 80% | 75% | 8 | 6.3s |
| gita-chapters | wiki | ✅ | ✅ | 33% | 100% | 6 | 4.5s |
| taj-mahal | wiki | ✅ | ✅ | 100% | 100% | 8 | 5.7s |
| isro-chandrayaan3 | wiki | ✅ | ✅ | 100% | 100% | 6 | 4.7s |
| hinglish-cuda | wiki | ✅ | ✅ | 78% | 43% | 8 | 32.6s |
| hindi-gandhi | wiki | ✅ | ✅ | 100% | 100% | 8 | 1.8s |
| llm-hallucination | academic | ✅ | ✅ | 56% | 100% | 8 | 6.8s |
| small-lms | academic | ✅ | ✅ | 88% | 100% | 8 | 6.4s |
| vector-db | all | ✅ | ✅ | 100% | 71% | 8 | 5.4s |
| dense-retrieval | academic | ✅ | ✅ | 86% | 100% | 8 | 4.2s |
| hn-rust | tech | ✅ | ✅ | 100% | 100% | 3 | 3.0s |
| hn-local-llm | tech | ✅ | ✅ | 100% | 100% | 8 | 5.6s |
| tcp-udp | wiki | ✅ | ✅ | 100% | 60% | 8 | 4.2s |
| inflation | wiki | ✅ | ✅ | 78% | 86% | 8 | 6.6s |
| ru-nvidia | wiki | ✅ | ✅ | 100% | 100% | 8 | 4.9s |
| es-moon | wiki | ✅ | ✅ | 67% | 50% | 8 | 6.4s |
| zh-nvidia | wiki | ✅ | ✅ | 0% | – | 8 | 3.9s |
| ar-moon | wiki | ✅ | ✅ | 100% | 100% | 8 | 3.9s |

History: [`backend/eval/results/history.csv`](backend/eval/results/history.csv). Questions: [`backend/eval/questions.jsonl`](backend/eval/questions.jsonl).
