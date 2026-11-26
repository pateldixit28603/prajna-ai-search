# Prajna benchmark

_Last run: 2026-11-26 15:24 UTC · mode: **NVIDIA NIM (24/24 answers by the LLM)** · 24 questions · runs automatically every day via GitHub Actions._

| Metric | Score | What it measures |
|---|---|---|
| Answer accuracy | **92%** | expected facts appear in the answer |
| Retrieval recall | **100%** | expected facts appear in retrieved sources |
| Citation coverage | **87%** | answer sentences carrying a [n] citation |
| Citation validity | **100%** | citations that point at a real source |
| Faithfulness (lexical) | **92%** | cited sentences supported by the cited passages |
| Latency p50 / p95 | **5.5s / 8.5s** | end-to-end, incl. live API calls |

## Per question

| id | focus | answer | sources | cites | faithful | sources used | time |
|---|---|---|---|---|---|---|---|
| nvidia-founded | wiki | ✅ | ✅ | 100% | 100% | 7 | 4.2s |
| cuda | wiki | ✅ | ✅ | 100% | 100% | 8 | 5.5s |
| transformer-paper | all | ✅ | ✅ | 100% | 100% | 8 | 2.9s |
| rag | all | ✅ | ✅ | 89% | 88% | 8 | 6.2s |
| bm25 | wiki | ✅ | ✅ | 80% | 100% | 4 | 2.9s |
| everest | wiki | ✅ | ✅ | 100% | 100% | 6 | 3.2s |
| photosynthesis | wiki | ❌ | ✅ | 100% | 83% | 6 | 5.6s |
| gita-chapters | wiki | ✅ | ✅ | 67% | 100% | 6 | 2.7s |
| taj-mahal | wiki | ✅ | ✅ | 100% | 100% | 8 | 8.5s |
| isro-chandrayaan3 | wiki | ✅ | ✅ | 100% | 100% | 6 | 3.0s |
| hinglish-cuda | wiki | ✅ | ✅ | 47% | 25% | 8 | 6.0s |
| hindi-gandhi | wiki | ✅ | ✅ | 100% | 100% | 8 | 6.8s |
| llm-hallucination | academic | ✅ | ✅ | 100% | 100% | 8 | 8.2s |
| small-lms | academic | ✅ | ✅ | 100% | 100% | 8 | 6.1s |
| vector-db | all | ✅ | ✅ | 100% | 88% | 8 | 6.8s |
| dense-retrieval | academic | ✅ | ✅ | 100% | 100% | 8 | 6.8s |
| hn-rust | tech | ✅ | ✅ | 100% | 100% | 6 | 7.3s |
| hn-local-llm | tech | ✅ | ✅ | 84% | 100% | 8 | 9.0s |
| tcp-udp | wiki | ✅ | ✅ | 50% | 71% | 8 | 3.8s |
| inflation | wiki | ❌ | ✅ | 100% | 100% | 8 | 3.1s |
| ru-nvidia | wiki | ✅ | ✅ | 100% | 100% | 8 | 2.6s |
| es-moon | wiki | ✅ | ✅ | 67% | 50% | 8 | 7.7s |
| zh-nvidia | wiki | ✅ | ✅ | 0% | – | 8 | 3.7s |
| ar-moon | wiki | ✅ | ✅ | 100% | 100% | 8 | 3.4s |

History: [`backend/eval/results/history.csv`](backend/eval/results/history.csv). Questions: [`backend/eval/questions.jsonl`](backend/eval/questions.jsonl).
