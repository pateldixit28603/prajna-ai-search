# Prajna benchmark

_Last run: 2026-11-26 15:07 UTC · mode: **NVIDIA NIM (24/24 answers by the LLM)** · 24 questions · runs automatically every day via GitHub Actions._

| Metric | Score | What it measures |
|---|---|---|
| Answer accuracy | **96%** | expected facts appear in the answer |
| Retrieval recall | **100%** | expected facts appear in retrieved sources |
| Citation coverage | **79%** | answer sentences carrying a [n] citation |
| Citation validity | **100%** | citations that point at a real source |
| Faithfulness (lexical) | **90%** | cited sentences supported by the cited passages |
| Latency p50 / p95 | **4.7s / 8.8s** | end-to-end, incl. live API calls |

## Per question

| id | focus | answer | sources | cites | faithful | sources used | time |
|---|---|---|---|---|---|---|---|
| nvidia-founded | wiki | ✅ | ✅ | 100% | 100% | 7 | 3.3s |
| cuda | wiki | ✅ | ✅ | 100% | 100% | 8 | 2.0s |
| transformer-paper | all | ✅ | ✅ | 100% | 100% | 8 | 1.9s |
| rag | all | ✅ | ✅ | 100% | 100% | 8 | 4.4s |
| bm25 | wiki | ✅ | ✅ | 80% | 100% | 4 | 4.2s |
| everest | wiki | ✅ | ✅ | 100% | 100% | 6 | 5.8s |
| photosynthesis | wiki | ❌ | ✅ | 100% | 78% | 8 | 6.8s |
| gita-chapters | wiki | ✅ | ✅ | 20% | 100% | 6 | 5.2s |
| taj-mahal | wiki | ✅ | ✅ | 100% | 100% | 8 | 5.3s |
| isro-chandrayaan3 | wiki | ✅ | ✅ | 100% | 100% | 6 | 1.9s |
| hinglish-cuda | wiki | ✅ | ✅ | 70% | 14% | 8 | 6.9s |
| hindi-gandhi | wiki | ✅ | ✅ | 100% | 100% | 8 | 4.7s |
| llm-hallucination | academic | ✅ | ✅ | 100% | 67% | 8 | 6.5s |
| small-lms | academic | ✅ | ✅ | 100% | 86% | 8 | 8.8s |
| vector-db | all | ✅ | ✅ | 86% | 100% | 8 | 27.5s |
| dense-retrieval | academic | ✅ | ✅ | 100% | 100% | 8 | 7.5s |
| hn-rust | tech | ✅ | ✅ | 90% | 100% | 6 | 6.6s |
| hn-local-llm | tech | ✅ | ✅ | 88% | 86% | 8 | 5.4s |
| tcp-udp | wiki | ✅ | ✅ | 47% | 43% | 8 | 4.3s |
| inflation | wiki | ✅ | ✅ | 100% | 100% | 8 | 3.1s |
| ru-nvidia | wiki | ✅ | ✅ | 100% | 100% | 8 | 4.0s |
| es-moon | wiki | ✅ | ✅ | 20% | 100% | 8 | 4.6s |
| zh-nvidia | wiki | ✅ | ✅ | 0% | – | 8 | 3.5s |
| ar-moon | wiki | ✅ | ✅ | 0% | – | 8 | 2.4s |

History: [`backend/eval/results/history.csv`](backend/eval/results/history.csv). Questions: [`backend/eval/questions.jsonl`](backend/eval/questions.jsonl).
