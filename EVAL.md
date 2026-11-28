# Prajna benchmark

_Last run: 2026-11-28 00:52 UTC · mode: **NVIDIA NIM (24/24 answers by the LLM)** · 24 questions · runs automatically every day via GitHub Actions._

| Metric | Score | What it measures |
|---|---|---|
| Answer accuracy | **100%** | expected facts appear in the answer |
| Retrieval recall | **100%** | expected facts appear in retrieved sources |
| Citation coverage | **94%** | answer sentences carrying a [n] citation |
| Citation validity | **100%** | citations that point at a real source |
| Faithfulness (lexical) | **88%** | cited sentences supported by the cited passages |
| Latency p50 / p95 | **3.3s / 5.8s** | end-to-end, incl. live API calls |

## Per question

| id | focus | answer | sources | cites | faithful | sources used | time |
|---|---|---|---|---|---|---|---|
| nvidia-founded | wiki | ✅ | ✅ | 100% | 100% | 8 | 3.3s |
| cuda | wiki | ✅ | ✅ | 100% | 100% | 8 | 3.7s |
| transformer-paper | all | ✅ | ✅ | 100% | 100% | 8 | 3.0s |
| rag | all | ✅ | ✅ | 94% | 38% | 8 | 5.4s |
| bm25 | wiki | ✅ | ✅ | 80% | 100% | 4 | 3.7s |
| everest | wiki | ✅ | ✅ | 100% | 100% | 6 | 1.7s |
| photosynthesis | wiki | ✅ | ✅ | 100% | 86% | 6 | 3.2s |
| gita-chapters | wiki | ✅ | ✅ | 100% | 100% | 6 | 1.9s |
| taj-mahal | wiki | ✅ | ✅ | 100% | 100% | 8 | 2.5s |
| isro-chandrayaan3 | wiki | ✅ | ✅ | 100% | 100% | 6 | 2.2s |
| hinglish-cuda | wiki | ✅ | ✅ | 88% | 29% | 8 | 5.0s |
| hindi-gandhi | wiki | ✅ | ✅ | 100% | 100% | 8 | 2.3s |
| llm-hallucination | academic | ✅ | ✅ | 100% | 100% | 8 | 4.9s |
| small-lms | academic | ✅ | ✅ | 89% | 88% | 8 | 5.8s |
| vector-db | all | ✅ | ✅ | 100% | 71% | 8 | 8.4s |
| dense-retrieval | academic | ✅ | ✅ | 100% | 100% | 8 | 3.8s |
| hn-rust | tech | ✅ | ✅ | 100% | 100% | 5 | 2.1s |
| hn-local-llm | tech | ✅ | ✅ | 71% | 100% | 8 | 3.5s |
| tcp-udp | wiki | ✅ | ✅ | 100% | 60% | 8 | 3.8s |
| inflation | wiki | ✅ | ✅ | 100% | 100% | 8 | 2.4s |
| ru-nvidia | wiki | ✅ | ✅ | 100% | 100% | 8 | 1.8s |
| es-moon | wiki | ✅ | ✅ | 40% | 50% | 8 | 3.4s |
| zh-nvidia | wiki | ✅ | ✅ | 100% | 100% | 8 | 2.2s |
| ar-moon | wiki | ✅ | ✅ | 100% | 100% | 8 | 3.1s |

History: [`backend/eval/results/history.csv`](backend/eval/results/history.csv). Questions: [`backend/eval/questions.jsonl`](backend/eval/questions.jsonl).
