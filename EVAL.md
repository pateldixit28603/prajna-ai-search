# Prajna benchmark

_Last run: 2026-11-26 20:23 UTC · mode: **NVIDIA NIM (24/24 answers by the LLM)** · 24 questions · runs automatically every day via GitHub Actions._

| Metric | Score | What it measures |
|---|---|---|
| Answer accuracy | **100%** | expected facts appear in the answer |
| Retrieval recall | **100%** | expected facts appear in retrieved sources |
| Citation coverage | **84%** | answer sentences carrying a [n] citation |
| Citation validity | **100%** | citations that point at a real source |
| Faithfulness (lexical) | **96%** | cited sentences supported by the cited passages |
| Latency p50 / p95 | **5.4s / 16.0s** | end-to-end, incl. live API calls |

## Per question

| id | focus | answer | sources | cites | faithful | sources used | time |
|---|---|---|---|---|---|---|---|
| nvidia-founded | wiki | ✅ | ✅ | 100% | 100% | 8 | 3.0s |
| cuda | wiki | ✅ | ✅ | 100% | 100% | 8 | 20.0s |
| transformer-paper | all | ✅ | ✅ | 100% | 100% | 8 | 3.0s |
| rag | all | ✅ | ✅ | 100% | 100% | 8 | 9.6s |
| bm25 | wiki | ✅ | ✅ | 80% | 100% | 4 | 5.6s |
| everest | wiki | ✅ | ✅ | 100% | 100% | 6 | 6.0s |
| photosynthesis | wiki | ✅ | ✅ | 100% | 75% | 6 | 5.2s |
| gita-chapters | wiki | ✅ | ✅ | 40% | 100% | 6 | 3.4s |
| taj-mahal | wiki | ✅ | ✅ | 83% | 100% | 8 | 10.7s |
| isro-chandrayaan3 | wiki | ✅ | ✅ | 100% | 100% | 6 | 6.5s |
| hinglish-cuda | wiki | ✅ | ✅ | 70% | 57% | 8 | 9.8s |
| hindi-gandhi | wiki | ✅ | ✅ | 100% | 100% | 8 | 3.1s |
| llm-hallucination | academic | ✅ | ✅ | 83% | 100% | 8 | 11.1s |
| small-lms | academic | ✅ | ✅ | 100% | 85% | 8 | 8.1s |
| vector-db | all | ✅ | ✅ | 100% | 100% | 8 | 16.0s |
| dense-retrieval | academic | ✅ | ✅ | 100% | 100% | 8 | 9.2s |
| hn-rust | tech | ✅ | ✅ | 100% | 100% | 6 | 4.4s |
| hn-local-llm | tech | ✅ | ✅ | 80% | 100% | 8 | 4.9s |
| tcp-udp | wiki | ✅ | ✅ | 53% | 88% | 8 | 8.4s |
| inflation | wiki | ✅ | ✅ | 100% | 100% | 8 | 4.7s |
| ru-nvidia | wiki | ✅ | ✅ | 100% | 100% | 8 | 4.1s |
| es-moon | wiki | ✅ | ✅ | 33% | 100% | 8 | 4.0s |
| zh-nvidia | wiki | ✅ | ✅ | 0% | – | 8 | 3.2s |
| ar-moon | wiki | ✅ | ✅ | 100% | 100% | 8 | 5.2s |

History: [`backend/eval/results/history.csv`](backend/eval/results/history.csv). Questions: [`backend/eval/questions.jsonl`](backend/eval/questions.jsonl).
