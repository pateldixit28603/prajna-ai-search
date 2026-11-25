# Prajna benchmark

_Last run: 2026-11-25 17:33 UTC · mode: **NVIDIA NIM (20/20 answers by the LLM)** · 20 questions · runs automatically every day via GitHub Actions._

| Metric | Score | What it measures |
|---|---|---|
| Answer accuracy | **95%** | expected facts appear in the answer |
| Retrieval recall | **100%** | expected facts appear in retrieved sources |
| Citation coverage | **49%** | answer sentences carrying a [n] citation |
| Citation validity | **75%** | citations that point at a real source |
| Faithfulness (lexical) | **70%** | cited sentences supported by the cited passages |
| Latency p50 / p95 | **3.3s / 6.3s** | end-to-end, incl. live API calls |

## Per question

| id | focus | answer | sources | cites | faithful | sources used | time |
|---|---|---|---|---|---|---|---|
| nvidia-founded | wiki | ✅ | ✅ | 0% | 0% | 8 | 2.2s |
| cuda | wiki | ✅ | ✅ | 100% | 100% | 8 | 2.2s |
| transformer-paper | all | ✅ | ✅ | 100% | 100% | 8 | 1.9s |
| rag | all | ✅ | ✅ | 100% | 100% | 8 | 3.2s |
| bm25 | wiki | ✅ | ✅ | 33% | 100% | 4 | 2.3s |
| everest | wiki | ✅ | ✅ | 50% | 100% | 6 | 1.5s |
| photosynthesis | wiki | ✅ | ✅ | 17% | 100% | 8 | 4.0s |
| gita-chapters | wiki | ✅ | ✅ | 0% | 0% | 6 | 3.4s |
| taj-mahal | wiki | ✅ | ✅ | 50% | 100% | 8 | 4.9s |
| isro-chandrayaan3 | wiki | ✅ | ✅ | 0% | 0% | 6 | 1.6s |
| hinglish-cuda | wiki | ✅ | ✅ | 0% | 0% | 8 | 3.4s |
| hindi-gandhi | wiki | ✅ | ✅ | 0% | 0% | 6 | 1.6s |
| llm-hallucination | academic | ✅ | ✅ | 62% | 100% | 8 | 5.4s |
| small-lms | academic | ✅ | ✅ | 75% | 100% | 8 | 6.3s |
| vector-db | all | ✅ | ✅ | 75% | 78% | 8 | 20.4s |
| dense-retrieval | academic | ✅ | ✅ | 31% | 80% | 8 | 4.2s |
| hn-rust | tech | ✅ | ✅ | 33% | 100% | 3 | 1.9s |
| hn-local-llm | tech | ✅ | ✅ | 77% | 100% | 8 | 5.7s |
| tcp-udp | wiki | ✅ | ✅ | 80% | 50% | 8 | 5.5s |
| inflation | wiki | ❌ | ✅ | 100% | 100% | 8 | 1.9s |

History: [`backend/eval/results/history.csv`](backend/eval/results/history.csv). Questions: [`backend/eval/questions.jsonl`](backend/eval/questions.jsonl).
