import numpy as np

from app.nvidia import ReasoningFilter, strip_reasoning
from app.retrieval.bm25 import BM25
from app.retrieval.fusion import mmr, rrf
from app.retrieval.text import chunk_text, tokenize


def test_tokenize_handles_hindi_and_stopwords():
    toks = tokenize("What is the NVIDIA GPU? एनवीडिया क्या है")
    assert "nvidia" in toks and "gpu" in toks and "the" not in toks
    assert "एनव" not in toks and any("ऀ" <= ch <= "ॿ" for t in toks for ch in t)


def test_chunker_respects_size_and_overlap():
    text = " ".join(f"Sentence number {i} talks about GPUs and parallel computing." for i in range(60))
    chunks = chunk_text(text, max_words=50, overlap=10)
    assert len(chunks) > 5
    assert all(len(c.split()) <= 60 for c in chunks)
    # overlap: last sentence of chunk k reappears at start of chunk k+1
    assert chunks[0].split(".")[-2].strip() in chunks[1]


def test_bm25_ranks_relevant_doc_first():
    bm = BM25(["bananas are yellow fruit", "nvidia makes gpus for ai", "cuda runs on nvidia gpus"])
    s = bm.scores("nvidia gpu cuda")
    assert s.index(max(s)) == 2 and s[0] == 0


def test_rrf_rewards_agreement():
    fused = rrf([[1, 2, 3], [2, 1, 3]])
    assert fused[1] == fused[2] > fused[3]


def test_mmr_prefers_diversity():
    vecs = np.array([[1, 0], [0.99, 0.01], [0.6, 0.8]], dtype=np.float32)
    picked = mmr([1, 0.2], vecs, [0, 1, 2], k=2, lam=0.5)
    assert picked[0] in (0, 1) and picked[1] == 2   # near-duplicate of the first pick is skipped


def test_reasoning_filter_across_token_boundaries():
    f = ReasoningFilter()
    out = "".join(f.feed(t) for t in ["Hi <th", "ink>secret", " stuff</thi", "nk>Answer", " here"]) + f.flush()
    assert out == "Hi Answer here"
    assert strip_reasoning("<think>x</think> ok") == "ok"


async def test_retired_endpoint_circuit_breaker(tmp_path):
    import httpx
    import pytest
    from app.nvidia import NvidiaClient, NvidiaError
    from conftest import make_settings
    calls = []

    def handler(req):
        calls.append(req.url.path)
        return httpx.Response(410, json={"title": "Gone"})
    nv = NvidiaClient(make_settings(tmp_path, key="k"), client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    for _ in range(3):
        with pytest.raises(NvidiaError):
            await nv.rerank("q", ["a", "b"])
    assert len(calls) == 1 and "rerank" in nv.dead
