# Prajna benchmark

_Last run: 2026-11-27 00:57 UTC · mode: **NVIDIA NIM (24/24 answers by the LLM)** · 24 questions · runs automatically every day via GitHub Actions._

| Metric | Score | What it measures |
|---|---|---|
| Answer accuracy | **100%** | expected facts appear in the answer |
| Retrieval recall | **100%** | expected facts appear in retrieved sources |
| Citation coverage | **84%** | answer sentences carrying a [n] citation |
| Citation validity | **100%** | citations that point at a real source |
| Faithfulness (lexical) | **92%** | cited sentences supported by the cited passages |
| Latency p50 / p95 | **5.7s / 8.1s** | end-to-end, incl. live API calls |

## Per question

| id | focus | answer | sources | cites | faithful | sources used | time |
|---|---|---|---|---|---|---|---|
| nvidia-founded | wiki | ✅ | ✅ | 100% | 100% | 7 | 4.1s |
| cuda | wiki | ✅ | ✅ | 100% | 100% | 8 | 7.3s |
| transformer-paper | all | ✅ | ✅ | 100% | 100% | 8 | 2.3s |
| rag | all | ✅ | ✅ | 100% | 100% | 8 | 5.2s |
| bm25 | wiki | ✅ | ✅ | 80% | 100% | 4 | 5.4s |
| everest | wiki | ✅ | ✅ | 100% | 100% | 6 | 3.5s |
| photosynthesis | wiki | ✅ | ✅ | 86% | 67% | 8 | 6.8s |
| gita-chapters | wiki | ✅ | ✅ | 100% | 100% | 6 | 7.9s |
| taj-mahal | wiki | ✅ | ✅ | 100% | 100% | 8 | 8.1s |
| isro-chandrayaan3 | wiki | ✅ | ✅ | 100% | 100% | 6 | 5.4s |
| hinglish-cuda | wiki | ✅ | ✅ | 31% | 40% | 8 | 5.7s |
| hindi-gandhi | wiki | ✅ | ✅ | 100% | 100% | 8 | 7.3s |
| llm-hallucination | academic | ✅ | ✅ | 100% | 100% | 8 | 7.9s |
| small-lms | academic | ✅ | ✅ | 94% | 100% | 8 | 8.8s |
| vector-db | all | ✅ | ✅ | 89% | 100% | 8 | 7.6s |
| dense-retrieval | academic | ✅ | ✅ | 100% | 100% | 8 | 4.8s |
| hn-rust | tech | ✅ | ✅ | 100% | 100% | 6 | 3.7s |
| hn-local-llm | tech | ✅ | ✅ | 60% | 100% | 8 | 8.1s |
| tcp-udp | wiki | ✅ | ✅ | 100% | 75% | 8 | 5.7s |
| inflation | wiki | ✅ | ✅ | 70% | 100% | 8 | 4.9s |
| ru-nvidia | wiki | ✅ | ✅ | 100% | 100% | 8 | 7.2s |
| es-moon | wiki | ✅ | ✅ | 100% | 50% | 8 | 4.8s |
| zh-nvidia | wiki | ✅ | ✅ | 0% | – | 8 | 6.3s |
| ar-moon | wiki | ✅ | ✅ | 0% | – | 8 | 5.5s |

History: [`backend/eval/results/history.csv`](backend/eval/results/history.csv). Questions: [`backend/eval/questions.jsonl`](backend/eval/questions.jsonl).
