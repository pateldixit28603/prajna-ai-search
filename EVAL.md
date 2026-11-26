# Prajna benchmark

_Last run: 2026-11-26 15:13 UTC · mode: **NVIDIA NIM (24/24 answers by the LLM)** · 24 questions · runs automatically every day via GitHub Actions._

| Metric | Score | What it measures |
|---|---|---|
| Answer accuracy | **100%** | expected facts appear in the answer |
| Retrieval recall | **100%** | expected facts appear in retrieved sources |
| Citation coverage | **88%** | answer sentences carrying a [n] citation |
| Citation validity | **100%** | citations that point at a real source |
| Faithfulness (lexical) | **91%** | cited sentences supported by the cited passages |
| Latency p50 / p95 | **4.4s / 11.8s** | end-to-end, incl. live API calls |

## Per question

| id | focus | answer | sources | cites | faithful | sources used | time |
|---|---|---|---|---|---|---|---|
| nvidia-founded | wiki | ✅ | ✅ | 100% | 100% | 7 | 3.8s |
| cuda | wiki | ✅ | ✅ | 100% | 100% | 8 | 4.2s |
| transformer-paper | all | ✅ | ✅ | 100% | 100% | 8 | 4.8s |
| rag | all | ✅ | ✅ | 100% | 100% | 8 | 4.5s |
| bm25 | wiki | ✅ | ✅ | 80% | 100% | 4 | 3.1s |
| everest | wiki | ✅ | ✅ | 100% | 100% | 6 | 3.1s |
| photosynthesis | wiki | ✅ | ✅ | 100% | 100% | 8 | 4.3s |
| gita-chapters | wiki | ✅ | ✅ | 33% | 100% | 6 | 3.1s |
| taj-mahal | wiki | ✅ | ✅ | 100% | 100% | 8 | 5.0s |
| isro-chandrayaan3 | wiki | ✅ | ✅ | 100% | 100% | 6 | 3.7s |
| hinglish-cuda | wiki | ✅ | ✅ | 56% | 20% | 8 | 6.9s |
| hindi-gandhi | wiki | ✅ | ✅ | 100% | 100% | 8 | 3.1s |
| llm-hallucination | academic | ✅ | ✅ | 86% | 100% | 8 | 9.8s |
| small-lms | academic | ✅ | ✅ | 94% | 100% | 8 | 6.4s |
| vector-db | all | ✅ | ✅ | 90% | 78% | 8 | 6.7s |
| dense-retrieval | academic | ✅ | ✅ | 100% | 100% | 8 | 5.3s |
| hn-rust | tech | ✅ | ✅ | 100% | 100% | 6 | 3.0s |
| hn-local-llm | tech | ✅ | ✅ | 64% | 100% | 8 | 12.4s |
| tcp-udp | wiki | ✅ | ✅ | 100% | 50% | 8 | 2.9s |
| inflation | wiki | ✅ | ✅ | 100% | 100% | 8 | 5.7s |
| ru-nvidia | wiki | ✅ | ✅ | 100% | 100% | 8 | 5.6s |
| es-moon | wiki | ✅ | ✅ | 100% | 50% | 8 | 3.8s |
| zh-nvidia | wiki | ✅ | ✅ | 0% | – | 8 | 3.6s |
| ar-moon | wiki | ✅ | ✅ | 100% | 100% | 8 | 11.8s |

History: [`backend/eval/results/history.csv`](backend/eval/results/history.csv). Questions: [`backend/eval/questions.jsonl`](backend/eval/questions.jsonl).
