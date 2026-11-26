"""AI image generation on NVIDIA's hosted visual-GenAI endpoints (FLUX / Stable Diffusion).

  prompt ──► (optional) prompt enhancer: Nemotron Bolt turns a short idea into a detailed image prompt
         ──► POST https://ai.api.nvidia.com/v1/genai/<publisher>/<model>
         ──► base64 image back to the browser as a data: URL (nothing is stored on disk)

Models are tried in order (IMAGE_MODELS); one that answers 404/403 (retired, or terms not accepted on
build.nvidia.com) is skipped for the rest of the process. The response shape differs per model family,
so the parser accepts every known shape: artifacts[0].base64, image, data[0].b64_json.
"""
from __future__ import annotations

import asyncio
import logging
import random
import re

import httpx

from .config import Settings

log = logging.getLogger("prajna.image")

ASPECTS = {   # name -> (width, height, aspect_ratio)
    "square": (1024, 1024, "1:1"),
    "landscape": (1344, 768, "16:9"),
    "portrait": (768, 1344, "9:16"),
}

ENHANCE_SYSTEM = """You write prompts for an AI image generator.
Turn the user's idea (any language) into ONE vivid English image prompt of at most 60 words:
subject, setting, style, lighting, composition. Keep every concrete detail the user gave.
Do not add text/letters to the image unless asked. Output ONLY the prompt."""


class ImageError(RuntimeError):
    def __init__(self, message: str, status: int = 502):
        super().__init__(message)
        self.status = status


def build_body(model: str, prompt: str, aspect: str, seed: int) -> dict:
    w, h, ratio = ASPECTS.get(aspect, ASPECTS["square"])
    if "stable-diffusion-3" in model:
        return {"prompt": prompt, "aspect_ratio": ratio, "cfg_scale": 5, "steps": 30, "seed": seed,
                "negative_prompt": "blurry, low quality, distorted, watermark"}
    # The hosted FLUX endpoints reject a "seed" field (HTTP 422 extra_forbidden, seen in nim_status.json)
    if "schnell" in model:
        return {"prompt": prompt, "width": w, "height": h, "steps": 4, "cfg_scale": 0, "mode": "base"}
    if "klein" in model:
        return {"prompt": prompt, "width": w, "height": h, "steps": 4}
    return {"prompt": prompt, "width": w, "height": h, "steps": 30, "cfg_scale": 3.5, "mode": "base"}


def parse_image(data: dict) -> tuple[str, str]:
    """Return (base64, finish_reason) from any known NVIDIA/OpenAI image response shape."""
    if isinstance(data.get("artifacts"), list) and data["artifacts"]:
        a = data["artifacts"][0]
        return a.get("base64") or "", str(a.get("finishReason") or a.get("finish_reason") or "")
    if isinstance(data.get("image"), str):
        return data["image"], str(data.get("finish_reason") or data.get("finishReason") or "")
    if isinstance(data.get("data"), list) and data["data"]:
        return data["data"][0].get("b64_json") or "", ""
    return "", ""


def mime_of(b64: str) -> str:
    if b64.startswith("iVBOR"):
        return "image/png"
    if b64.startswith("UklGR"):
        return "image/webp"
    return "image/jpeg"


class ImageGenerator:
    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None):
        self.s = settings
        self._client = client or httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=10.0))
        self.dead: set[str] = set()

    @property
    def enabled(self) -> bool:
        return bool(self.s.nvidia_api_key) or "localhost" in self.s.image_base_url

    def models(self) -> list[str]:
        return [m for m in self.s.image_models if m not in self.dead]

    async def enhance(self, nv, idea: str) -> str:
        """Nemotron Bolt rewrites a short idea into a detailed prompt. Falls back to the idea itself."""
        if not nv.enabled:
            return idea
        try:
            out = await asyncio.wait_for(nv.chat(
                [{"role": "system", "content": ENHANCE_SYSTEM}, {"role": "user", "content": idea}],
                model=self.s.llm_fast_model, temperature=0.6, max_tokens=160), timeout=10)
            out = re.sub(r"^prompt:\s*", "", out.strip(), flags=re.I).strip().strip('"').strip()
            if len(out) <= 10 or out[:1] in "{[<":     # empty or not a plain-text prompt
                return idea
            return out[:900]
        except Exception as e:
            log.warning("prompt enhance failed: %s", e)
            return idea

    async def generate(self, prompt: str, aspect: str = "square", seed: int | None = None) -> dict:
        if not self.enabled:
            raise ImageError("Image generation needs an NVIDIA API key (NVIDIA_API_KEY).", 503)
        seed = seed if seed is not None else random.randint(1, 2**31 - 1)
        headers = {"Authorization": f"Bearer {self.s.nvidia_api_key}", "Accept": "application/json",
                   "Content-Type": "application/json"}
        errors: list[str] = []
        for model in self.models():
            url = f"{self.s.image_base_url.rstrip('/')}/{model}"
            body = build_body(model, prompt, aspect, seed)
            try:
                r = await self._client.post(url, headers=headers, json=body)
                if r.status_code == 422:      # schema differs: retry with the minimal common body
                    w, h, _ = ASPECTS.get(aspect, ASPECTS["square"])
                    r = await self._client.post(url, headers=headers, json={"prompt": prompt, "width": w, "height": h})
                    if r.status_code == 422:
                        r = await self._client.post(url, headers=headers,
                                                    json={"prompt": prompt, "width": 1024, "height": 1024})
            except httpx.HTTPError as e:
                errors.append(f"{model}: {type(e).__name__}")
                continue
            if r.status_code == 202:          # NVCF queued the job: poll until the image is ready
                r = await self._poll(r, headers)
            if r.status_code in (401,):
                raise ImageError("NVIDIA rejected the API key for image generation.", 502)
            if r.status_code in (403, 404, 410):
                self.dead.add(model)
                errors.append(f"{model}: HTTP {r.status_code}")
                continue
            if r.status_code == 429:
                raise ImageError("NVIDIA image service is busy (rate limit). Try again in a minute.", 429)
            if r.status_code >= 400:
                errors.append(f"{model}: HTTP {r.status_code} {r.text[:120]}")
                continue
            b64, finish = parse_image(r.json())
            if "FILTER" in finish.upper():
                raise ImageError("NVIDIA's safety filter blocked this image. Try a different prompt.", 400)
            if not b64:
                errors.append(f"{model}: empty image")
                continue
            w, h, _ = ASPECTS.get(aspect, ASPECTS["square"])
            return {"image": f"data:{mime_of(b64)};base64,{b64}", "model": model, "seed": seed,
                    "aspect": aspect, "width": w, "height": h}
        log.warning("image generation failed: %s", errors)
        raise ImageError("No NVIDIA image model answered right now. " + "; ".join(errors)[:300], 502)

    async def _poll(self, r: httpx.Response, headers: dict, deadline: float = 80.0) -> httpx.Response:
        req_id = r.headers.get("NVCF-REQID") or r.headers.get("nvcf-reqid")
        if not req_id:
            return r
        url = f"{self.s.image_status_url.rstrip('/')}/{req_id}"
        waited = 0.0
        while waited < deadline:
            await asyncio.sleep(1.5)
            waited += 1.5
            r = await self._client.get(url, headers=headers)
            if r.status_code != 202:
                return r
        return httpx.Response(504, text="image job still queued")

    async def aclose(self) -> None:
        await self._client.aclose()
