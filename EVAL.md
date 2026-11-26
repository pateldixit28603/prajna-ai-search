# Prajna benchmark

_Last run: 2026-11-26 00:56 UTC · mode: **NVIDIA NIM (24/24 answers by the LLM)** · 24 questions · runs automatically every day via GitHub Actions._

| Metric | Score | What it measures |
|---|---|---|
| Answer accuracy | **100%** | expected facts appear in the answer |
| Retrieval recall | **100%** | expected facts appear in retrieved sources |
| Citation coverage | **96%** | answer sentences carrying a [n] citation |
| Citation validity | **100%** | citations that point at a real source |
| Faithfulness (lexical) | **89%** | cited sentences supported by the cited passages |
| Latency p50 / p95 | **3.4s / 6.1s** | end-to-end, incl. live API calls |

## Per question

| id | focus | answer | sources | cites | faithful | sources used | time |
|---|---|---|---|---|---|---|---|
| nvidia-founded | wiki | ✅ | ✅ | 100% | 100% | 8 | 3.0s |
| cuda | wiki | ✅ | ✅ | 100% | 100% | 8 | 2.3s |
| transformer-paper | all | ✅ | ✅ | 100% | 100% | 8 | 1.8s |
| rag | all | ✅ | ✅ | 100% | 100% | 8 | 2.7s |
| bm25 | wiki | ✅ | ✅ | 80% | 100% | 4 | 6.1s |
| everest | wiki | ✅ | ✅ | 100% | 100% | 6 | 5.1s |
| photosynthesis | wiki | ✅ | ✅ | 100% | 100% | 8 | 6.1s |
| gita-chapters | wiki | ✅ | ✅ | 100% | 100% | 6 | 3.4s |
| taj-mahal | wiki | ✅ | ✅ | 100% | 100% | 8 | 3.3s |
| isro-chandrayaan3 | wiki | ✅ | ✅ | 100% | 100% | 6 | 3.8s |
| hinglish-cuda | wiki | ✅ | ✅ | 42% | 20% | 8 | 4.7s |
| hindi-gandhi | wiki | ✅ | ✅ | 100% | 100% | 8 | 1.8s |
| llm-hallucination | academic | ✅ | ✅ | 100% | 100% | 8 | 3.5s |
| small-lms | academic | ✅ | ✅ | 100% | 100% | 8 | 3.7s |
| vector-db | all | ✅ | ✅ | 100% | 100% | 8 | 5.1s |
| dense-retrieval | academic | ✅ | ✅ | 100% | 100% | 8 | 4.2s |
| hn-rust | tech | ✅ | ✅ | 100% | 100% | 5 | 2.0s |
| hn-local-llm | tech | ✅ | ✅ | 76% | 92% | 8 | 5.2s |
| tcp-udp | wiki | ✅ | ✅ | 100% | 83% | 8 | 3.2s |
| inflation | wiki | ✅ | ✅ | 100% | 100% | 8 | 2.2s |
| ru-nvidia | wiki | ✅ | ✅ | 100% | 100% | 8 | 1.7s |
| es-moon | wiki | ✅ | ✅ | 100% | 50% | 8 | 2.4s |
| zh-nvidia | wiki | ✅ | ✅ | 100% | 0% | 8 | 1.6s |
| ar-moon | wiki | ✅ | ✅ | 100% | 100% | 8 | 5.5s |

History: [`backend/eval/results/history.csv`](backend/eval/results/history.csv). Questions: [`backend/eval/questions.jsonl`](backend/eval/questions.jsonl).
