"""NVIDIA NIM client: LLM chat (streaming), NeMo Retriever embeddings, and reranking.

All three talk plain HTTP so the exact same code works with:
  - hosted NVIDIA API catalog  (https://integrate.api.nvidia.com/v1  + nvapi-... key)
  - self-hosted NIM containers  (http://localhost:8000/v1 etc, running on your own GPU)
"""
from __future__ import annotations

import json
import logging
from typing import AsyncIterator, Sequence

import httpx

from .config import Settings

log = logging.getLogger("prajna.nvidia")


class NvidiaError(RuntimeError):
    pass


class NvidiaClient:
    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None):
        self.s = settings
        self._client = client or httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0))

    # ------------------------------------------------------------------ utils
    def _headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.s.nvidia_api_key:
            h["Authorization"] = f"Bearer {self.s.nvidia_api_key}"
        return h

    @property
    def enabled(self) -> bool:
        return self.s.nvidia_enabled

    async def aclose(self) -> None:
        await self._client.aclose()

    # ------------------------------------------------------------------- chat
    async def chat(self, messages: list[dict], *, model: str | None = None,
                   temperature: float = 0.2, max_tokens: int = 512) -> str:
        """Non-streaming completion (used for query rewriting / follow-ups)."""
        payload = {
            "model": model or self.s.llm_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        r = await self._client.post(f"{self.s.llm_base_url}/chat/completions", headers=self._headers(), json=payload)
        if r.status_code >= 400:
            raise NvidiaError(f"LLM HTTP {r.status_code}: {r.text[:300]}")
        data = r.json()
        return strip_reasoning(data["choices"][0]["message"].get("content") or "")

    async def chat_stream(self, messages: list[dict], *, model: str | None = None,
                          temperature: float = 0.2, max_tokens: int = 1400) -> AsyncIterator[str]:
        """Streams answer tokens via Server-Sent Events from the NIM endpoint."""
        payload = {
            "model": model or self.s.llm_model,
            "messages": messages,
            "temperature": temperature,
            "top_p": 0.9,
            "max_tokens": max_tokens,
            "stream": True,
        }
        headers = self._headers() | {"Accept": "text/event-stream"}
        filt = ReasoningFilter()
        async with self._client.stream("POST", f"{self.s.llm_base_url}/chat/completions",
                                       headers=headers, json=payload) as r:
            if r.status_code >= 400:
                body = (await r.aread()).decode(errors="ignore")
                raise NvidiaError(f"LLM HTTP {r.status_code}: {body[:300]}")
            async for line in r.aiter_lines():
                if not line.startswith("data:"):
                    continue
                chunk = line[5:].strip()
                if chunk == "[DONE]":
                    break
                try:
                    delta = json.loads(chunk)["choices"][0].get("delta", {})
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
                # Reasoning models may send `reasoning_content`; we only surface the final answer.
                text = delta.get("content")
                if text:
                    out = filt.feed(text)
                    if out:
                        yield out
        tail = filt.flush()
        if tail:
            yield tail

    # ------------------------------------------------------------- embeddings
    async def embed(self, texts: Sequence[str], input_type: str = "passage") -> list[list[float]]:
        """NeMo Retriever embeddings. input_type must be 'query' or 'passage' (asymmetric model)."""
        out: list[list[float]] = []
        for i in range(0, len(texts), 32):
            batch = [t[:6000] for t in texts[i:i + 32]]
            payload = {
                "model": self.s.embed_model,
                "input": batch,
                "input_type": input_type,
                "encoding_format": "float",
                "truncate": "END",
            }
            r = await self._client.post(f"{self.s.embed_base_url}/embeddings", headers=self._headers(), json=payload)
            if r.status_code >= 400:
                raise NvidiaError(f"Embed HTTP {r.status_code}: {r.text[:300]}")
            data = sorted(r.json()["data"], key=lambda d: d["index"])
            out.extend(d["embedding"] for d in data)
        return out

    # ---------------------------------------------------------------- rerank
    async def rerank(self, query: str, passages: Sequence[str]) -> list[float]:
        """Returns one relevance logit per passage (same order as input)."""
        if not passages:
            return []
        payload = {
            "model": self.s.rerank_model,
            "query": {"text": query},
            "passages": [{"text": p[:4000]} for p in passages],
            "truncate": "END",
        }
        r = await self._client.post(self.s.rerank_url, headers=self._headers(), json=payload)
        if r.status_code >= 400:
            raise NvidiaError(f"Rerank HTTP {r.status_code}: {r.text[:300]}")
        scores = [float("-inf")] * len(passages)
        for item in r.json().get("rankings", []):
            scores[item["index"]] = float(item["logit"])
        return scores


def strip_reasoning(text: str) -> str:
    """Remove <think>...</think> blocks some reasoning models emit."""
    while "<think>" in text and "</think>" in text:
        a = text.index("<think>")
        b = text.index("</think>") + len("</think>")
        text = text[:a] + text[b:]
    return text.strip()


class ReasoningFilter:
    """Streaming filter that hides <think>...</think> spans across token boundaries."""

    OPEN, CLOSE = "<think>", "</think>"

    def __init__(self) -> None:
        self.buf = ""
        self.inside = False

    def feed(self, text: str) -> str:
        self.buf += text
        out = []
        while True:
            if self.inside:
                i = self.buf.find(self.CLOSE)
                if i == -1:
                    # keep only a possible partial close tag
                    self.buf = self.buf[-(len(self.CLOSE) - 1):]
                    break
                self.buf = self.buf[i + len(self.CLOSE):].lstrip("\n")
                self.inside = False
            else:
                i = self.buf.find(self.OPEN)
                if i == -1:
                    # emit everything except a possible partial open tag at the end
                    keep = 0
                    for k in range(1, len(self.OPEN)):
                        if self.buf.endswith(self.OPEN[:k]):
                            keep = k
                    out.append(self.buf[:len(self.buf) - keep])
                    self.buf = self.buf[len(self.buf) - keep:]
                    break
                out.append(self.buf[:i])
                self.buf = self.buf[i + len(self.OPEN):]
                self.inside = True
        return "".join(out)

    def flush(self) -> str:
        rest = "" if self.inside else self.buf
        self.buf = ""
        return rest
