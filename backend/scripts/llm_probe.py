"""Probe how the configured NIM chat model streams: content vs reasoning tokens, finish reason,
for several 'thinking' settings. Writes backend/eval/results/llm_probe.json (no secrets)."""
from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.config import settings  # noqa: E402

CTX = ("[1] Nvidia (wikipedia)\nNvidia Corporation is an American technology company founded in 1993 by Jensen Huang, "
       "Chris Malachowsky and Curtis Priem. It designs GPUs.\n\nQuestion: When was Nvidia founded and by whom?")
SYSTEM = "Answer using only the numbered results and cite like [1]. Be concise."

VARIANTS = {
    "plain": {},
    "no_think_sys": {"_sys_suffix": "\n/no_think"},
    "template_enable_thinking_false": {"chat_template_kwargs": {"enable_thinking": False}},
    "template_thinking_false": {"chat_template_kwargs": {"thinking": False}},
    "reasoning_effort_low": {"reasoning_effort": "low"},
    "reasoning_budget_0": {"nvext": {"max_thinking_tokens": 0}},
}


async def run(c: httpx.AsyncClient, model: str, name: str, extra: dict) -> dict:
    extra = dict(extra)
    suffix = extra.pop("_sys_suffix", "")
    payload = {"model": model, "stream": True, "max_tokens": 1400, "temperature": 0.2,
               "messages": [{"role": "system", "content": SYSTEM + suffix}, {"role": "user", "content": CTX}], **extra}
    t0 = time.perf_counter()
    content, reasoning, finish, status, err = "", "", None, None, ""
    try:
        async with c.stream("POST", f"{settings.llm_base_url}/chat/completions", json=payload, headers={
                "Authorization": f"Bearer {settings.nvidia_api_key}", "Accept": "text/event-stream"}) as r:
            status = r.status_code
            if status >= 400:
                err = (await r.aread()).decode(errors="ignore")[:200]
            else:
                async for line in r.aiter_lines():
                    if not line.startswith("data:") or line[5:].strip() == "[DONE]":
                        continue
                    ch = json.loads(line[5:])["choices"][0]
                    d = ch.get("delta", {})
                    content += d.get("content") or ""
                    reasoning += d.get("reasoning_content") or d.get("reasoning") or ""
                    finish = ch.get("finish_reason") or finish
    except Exception as e:
        err = f"{type(e).__name__}: {e}"[:200]
    return {"model": model, "variant": name, "status": status, "finish": finish, "secs": round(time.perf_counter() - t0, 1),
            "content_chars": len(content), "reasoning_chars": len(reasoning), "has_think_tag": "<think>" in content,
            "content_head": content[:160], "error": err}


async def main() -> None:
    out = []
    async with httpx.AsyncClient(timeout=90) as c:
        for model in dict.fromkeys([settings.llm_model, settings.llm_fast_model]):
            for name, extra in VARIANTS.items():
                r = await run(c, model, name, extra)
                out.append(r)
                print(r["model"], r["variant"], r["status"], r["finish"], r["secs"], "content", r["content_chars"],
                      "reasoning", r["reasoning_chars"], r["error"][:80])
    p = ROOT / "eval" / "results" / "llm_probe.json"
    p.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
