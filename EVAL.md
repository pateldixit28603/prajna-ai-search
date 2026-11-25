# Prajna benchmark

_Last run: 2026-11-25 17:41 UTC · mode: **NVIDIA NIM (20/20 answers by the LLM)** · 20 questions · runs automatically every day via GitHub Actions._

| Metric | Score | What it measures |
|---|---|---|
| Answer accuracy | **100%** | expected facts appear in the answer |
| Retrieval recall | **100%** | expected facts appear in retrieved sources |
| Citation coverage | **94%** | answer sentences carrying a [n] citation |
| Citation validity | **100%** | citations that point at a real source |
| Faithfulness (lexical) | **86%** | cited sentences supported by the cited passages |
| Latency p50 / p95 | **5.3s / 8.2s** | end-to-end, incl. live API calls |

## Per question

| id | focus | answer | sources | cites | faithful | sources used | time |
|---|---|---|---|---|---|---|---|
| nvidia-founded | wiki | ✅ | ✅ | 100% | 100% | 8 | 3.9s |
| cuda | wiki | ✅ | ✅ | 100% | 100% | 8 | 5.8s |
| transformer-paper | all | ✅ | ✅ | 100% | 75% | 8 | 2.5s |
| rag | all | ✅ | ✅ | 100% | 100% | 8 | 5.9s |
| bm25 | wiki | ✅ | ✅ | 83% | 100% | 4 | 5.5s |
| everest | wiki | ✅ | ✅ | 100% | 100% | 6 | 5.3s |
| photosynthesis | wiki | ✅ | ✅ | 89% | 88% | 8 | 3.3s |
| gita-chapters | wiki | ✅ | ✅ | 100% | 100% | 6 | 1.8s |
| taj-mahal | wiki | ✅ | ✅ | 100% | 100% | 8 | 3.7s |
| isro-chandrayaan3 | wiki | ✅ | ✅ | 100% | 100% | 6 | 2.7s |
| hinglish-cuda | wiki | ✅ | ✅ | 40% | 17% | 8 | 9.2s |
| hindi-gandhi | wiki | ✅ | ✅ | 100% | 0% | 6 | 3.3s |
| llm-hallucination | academic | ✅ | ✅ | 100% | 100% | 8 | 5.9s |
| small-lms | academic | ✅ | ✅ | 100% | 100% | 8 | 6.3s |
| vector-db | all | ✅ | ✅ | 82% | 89% | 8 | 8.2s |
| dense-retrieval | academic | ✅ | ✅ | 100% | 100% | 8 | 3.2s |
| hn-rust | tech | ✅ | ✅ | 100% | 100% | 6 | 4.5s |
| hn-local-llm | tech | ✅ | ✅ | 83% | 100% | 8 | 6.9s |
| tcp-udp | wiki | ✅ | ✅ | 100% | 43% | 8 | 5.6s |
| inflation | wiki | ✅ | ✅ | 100% | 100% | 8 | 5.2s |

History: [`backend/eval/results/history.csv`](backend/eval/results/history.csv). Questions: [`backend/eval/questions.jsonl`](backend/eval/questions.jsonl).
