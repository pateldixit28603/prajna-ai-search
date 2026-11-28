import json
import re
import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import Settings  # noqa: E402
from app.nvidia import NvidiaClient  # noqa: E402
from app.sources.base import Document  # noqa: E402


class FakeSource:
    def __init__(self, name, docs):
        self.name, self.label, self.docs = name, name, docs

    async def search(self, query, limit):
        return self.docs[:limit]


class BrokenSource:
    name = label = "broken"

    async def search(self, query, limit):
        raise httpx.ConnectError("down")


DOCS = [
    Document(title="NVIDIA", url="https://en.wikipedia.org/wiki/Nvidia", source="wikipedia",
             content="Nvidia Corporation is an American technology company headquartered in Santa Clara, California. "
                     "It was founded in 1993 by Jensen Huang, Chris Malachowsky and Curtis Priem. "
                     "Nvidia designs graphics processing units for gaming and professional markets."),
    Document(title="CUDA", url="https://en.wikipedia.org/wiki/CUDA", source="wikipedia",
             content="CUDA is a parallel computing platform and programming model created by Nvidia in 2006. "
                     "It allows software developers to use a GPU for general purpose processing."),
    Document(title="Banana", url="https://en.wikipedia.org/wiki/Banana", source="wikipedia",
             content="A banana is an elongated edible fruit produced by several kinds of large herbaceous plants."),
]


def make_settings(tmp_path, key=""):
    s = Settings()
    s.nvidia_api_key = key
    s.llm_base_url = "https://nim.test/v1"
    s.embed_base_url = "https://nim.test/v1"
    s.rerank_url = "https://nim.test/v1/ranking"
    s.data_dir = tmp_path
    return s


def nim_transport():
    """Fake NVIDIA NIM: chat (stream + non-stream), embeddings, ranking."""
    def handler(req: httpx.Request):
        body = json.loads(req.content or b"{}")
        if req.url.path.endswith("/embeddings"):
            vecs = []
            for t in body["input"]:
                t = t.lower()
                vecs.append([t.count("nvidia") + t.count("founded"), t.count("cuda"), t.count("banana"), 0.1])
            return httpx.Response(200, json={"data": [{"index": i, "embedding": v} for i, v in enumerate(vecs)]})
        if req.url.path.endswith("/ranking"):
            ranks = [{"index": i, "logit": (5.0 if "founded" in p["text"] else -1.0 * i)}
                     for i, p in enumerate(body["passages"])]
            return httpx.Response(200, json={"rankings": sorted(ranks, key=lambda r: -r["logit"])})
        if req.url.path.endswith("/chat/completions"):
            sys_prompt = body["messages"][0]["content"]
            if body.get("stream"):
                parts = ["<think>hidden reasoning</think>", "Nvidia was ", "founded in 1993 ", "[1]."]
                lines = "".join(
                    f"data: {json.dumps({'choices': [{'delta': {'content': p}}]})}\n\n" for p in parts)
                return httpx.Response(200, text=lines + "data: [DONE]\n\n",
                                      headers={"content-type": "text/event-stream"})
            if "translator" in sys_prompt:
                # simulate a sloppy translation: drops [1], invents a non-existent source [9]
                src = body["messages"][1]["content"]
                out = src.replace("Nvidia was founded in 1993", "Nvidia fue fundada en 1993")
                out = out.replace("[1]", "[9]")
                return httpx.Response(200, json={"choices": [{"message": {"content": out}}]})
            if "fact-checker" in sys_prompt:
                user = body["messages"][1]["content"]
                claim = user.split("\n", 1)[0]
                rows = []
                for m in re.finditer(r"^\[(\d+)\] (.*?)(?=^\[\d+\] |\Z)", user, re.M | re.S):
                    block = m.group(2)
                    st = "neutral"
                    if "founded in 1993" in block:
                        st = "supports" if "1993" in claim else "contradicts"
                    rows.append({"n": int(m.group(1)), "stance": st, "reason": "fake reason"})
                rows.append({"n": 99, "stance": "supports", "reason": "invented passage"})
                content = json.dumps({"stances": rows, "summary": "Founding year per [1]; bogus [42]."})
                return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})
            content = ('{"queries": ["nvidia founding year"]}' if "search queries" in sys_prompt
                       else '{"questions": ["Who founded Nvidia?", "What is CUDA?", "Nvidia GPUs?"]}')
            return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})
        return httpx.Response(404)
    return httpx.MockTransport(handler)


@pytest.fixture
def docs():
    return DOCS


@pytest.fixture
def offline_nv(tmp_path):
    s = make_settings(tmp_path)
    return s, NvidiaClient(s)


@pytest.fixture
def online_nv(tmp_path):
    s = make_settings(tmp_path, key="nvapi-test")
    return s, NvidiaClient(s, client=httpx.AsyncClient(transport=nim_transport()))
