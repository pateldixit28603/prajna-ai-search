# Prajna benchmark

_Last run: 2026-11-27 01:45 UTC · mode: **NVIDIA NIM (24/24 answers by the LLM)** · 24 questions · runs automatically every day via GitHub Actions._

| Metric | Score | What it measures |
|---|---|---|
| Answer accuracy | **96%** | expected facts appear in the answer |
| Retrieval recall | **100%** | expected facts appear in retrieved sources |
| Citation coverage | **82%** | answer sentences carrying a [n] citation |
| Citation validity | **100%** | citations that point at a real source |
| Faithfulness (lexical) | **88%** | cited sentences supported by the cited passages |
| Latency p50 / p95 | **7.3s / 11.3s** | end-to-end, incl. live API calls |

## Per question

| id | focus | answer | sources | cites | faithful | sources used | time |
|---|---|---|---|---|---|---|---|
| nvidia-founded | wiki | ✅ | ✅ | 100% | 100% | 7 | 8.5s |
| cuda | wiki | ✅ | ✅ | 100% | 100% | 8 | 7.3s |
| transformer-paper | all | ✅ | ✅ | 100% | 75% | 8 | 2.7s |
| rag | all | ✅ | ✅ | 100% | 100% | 8 | 7.3s |
| bm25 | wiki | ✅ | ✅ | 80% | 100% | 4 | 7.3s |
| everest | wiki | ✅ | ✅ | 100% | 100% | 6 | 5.5s |
| photosynthesis | wiki | ❌ | ✅ | 100% | 100% | 8 | 7.2s |
| gita-chapters | wiki | ✅ | ✅ | 33% | 100% | 6 | 35.0s |
| taj-mahal | wiki | ✅ | ✅ | 100% | 100% | 8 | 7.7s |
| isro-chandrayaan3 | wiki | ✅ | ✅ | 100% | 100% | 6 | 8.4s |
| hinglish-cuda | wiki | ✅ | ✅ | 83% | 40% | 8 | 9.1s |
| hindi-gandhi | wiki | ✅ | ✅ | 100% | 100% | 8 | 4.6s |
| llm-hallucination | academic | ✅ | ✅ | 82% | 100% | 8 | 8.7s |
| small-lms | academic | ✅ | ✅ | 100% | 100% | 8 | 8.1s |
| vector-db | all | ✅ | ✅ | 93% | 100% | 8 | 11.3s |
| dense-retrieval | academic | ✅ | ✅ | 100% | 100% | 8 | 4.1s |
| hn-rust | tech | ✅ | ✅ | 86% | 83% | 5 | 7.1s |
| hn-local-llm | tech | ✅ | ✅ | 81% | 92% | 8 | 9.7s |
| tcp-udp | wiki | ✅ | ✅ | 100% | 50% | 8 | 3.9s |
| inflation | wiki | ✅ | ✅ | 100% | 100% | 8 | 6.2s |
| ru-nvidia | wiki | ✅ | ✅ | 100% | 50% | 6 | 4.7s |
| es-moon | wiki | ✅ | ✅ | 40% | 50% | 8 | 8.4s |
| zh-nvidia | wiki | ✅ | ✅ | 0% | – | 8 | 4.9s |
| ar-moon | wiki | ✅ | ✅ | 0% | – | 8 | 5.0s |

History: [`backend/eval/results/history.csv`](backend/eval/results/history.csv). Questions: [`backend/eval/questions.jsonl`](backend/eval/questions.jsonl).
