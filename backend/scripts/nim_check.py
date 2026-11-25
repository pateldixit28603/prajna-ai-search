"""Check every configured NVIDIA endpoint and record which ones work (never prints the key).

Writes backend/eval/results/nim_status.json and exits 0 even on failure so the daily job continues.
If the configured answer model fails, it also probes a few fallback chat models and reports which work.
"""
from __future__ import annotations

import asyncio
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import settings  # noqa: E402
from app.nvidia import NvidiaClient  # noqa: E402

FALLBACK_CHAT = [
    "meta/llama-3.3-70b-instruct",
    "meta/llama-3.1-8b-instruct",
    "nvidia/llama-3.3-nemotron-super-49b-v1.5",
    "nvidia/nvidia-nemotron-nano-9b-v2",
    "nvidia/llama-3.1-nemotron-nano-8b-v1",
    "mistralai/mistral-small-24b-instruct",
]


async def probe(name: str, coro) -> dict:
    try:
        out = await asyncio.wait_for(coro, timeout=45)
        return {"check": name, "ok": True, "detail": str(out)[:80]}
    except Exception as e:
        return {"check": name, "ok": False, "detail": f"{type(e).__name__}: {str(e)[:220]}"}


async def main() -> None:
    nv = NvidiaClient(settings)
    msg = [{"role": "user", "content": "Reply with the single word: ready"}]
    results = [
        await probe(f"chat:{settings.llm_model}", nv.chat(msg, max_tokens=400)),
        await probe(f"chat:{settings.llm_fast_model}", nv.chat(msg, model=settings.llm_fast_model, max_tokens=400)),
        await probe(f"embed:{settings.embed_model}", nv.embed(["hello world"], input_type="query")),
        await probe(f"rerank:{settings.rerank_model}", nv.rerank("gpu", ["CUDA runs on GPUs", "bananas"])),
    ]
    if not results[0]["ok"] or not results[1]["ok"]:
        for m in FALLBACK_CHAT:
            results.append(await probe(f"chat:{m}", nv.chat(msg, model=m, max_tokens=400)))
    await nv.aclose()
    status = {"date": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
              "key_present": bool(settings.nvidia_api_key), "results": results}
    out = ROOT / "eval" / "results" / "nim_status.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(status, indent=2), encoding="utf-8")
    for r in results:
        print(("OK  " if r["ok"] else "FAIL"), r["check"], "-", r["detail"])


if __name__ == "__main__":
    asyncio.run(main())
