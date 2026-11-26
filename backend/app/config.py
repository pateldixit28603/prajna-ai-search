"""Central configuration, read from environment variables (or a .env file).

Every NVIDIA endpoint is configurable, so the same code runs against:
  * the hosted NVIDIA API catalog (build.nvidia.com) with an `nvapi-...` key, or
  * self-hosted NIM containers on your own NVIDIA GPU (see deploy/docker-compose.gpu.yml).
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path


def _load_dotenv(path: Path) -> None:
    """Tiny .env loader so we don't need python-dotenv."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


BASE_DIR = Path(__file__).resolve().parent.parent
_load_dotenv(BASE_DIR / ".env")
_load_dotenv(BASE_DIR.parent / ".env")


def _bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class Settings:
    # ---- NVIDIA NIM -------------------------------------------------------
    nvidia_api_key: str = field(default_factory=lambda: os.getenv("NVIDIA_API_KEY", ""))
    # OpenAI-compatible LLM endpoint (hosted or local NIM)
    llm_base_url: str = field(default_factory=lambda: os.getenv("LLM_BASE_URL", "https://integrate.api.nvidia.com/v1"))
    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b"))
    # Smaller/faster model for query rewriting + follow-up questions
    llm_fast_model: str = field(default_factory=lambda: os.getenv("LLM_FAST_MODEL", "nvidia/nemotron-3.5-bolt-e4b"))
    # Extra JSON merged into every chat request. Nemotron 3.5 models "think" by default, which burns the
    # token budget before the answer; disabling it gives direct answers ~7x faster (see scripts/llm_probe.py).
    llm_extra_body: dict = field(default_factory=lambda: json.loads(
        os.getenv("LLM_EXTRA_BODY", '{"chat_template_kwargs": {"enable_thinking": false}}') or "{}"))
    # NeMo Retriever embeddings (OpenAI-compatible /embeddings)
    embed_base_url: str = field(default_factory=lambda: os.getenv("EMBED_BASE_URL", "https://integrate.api.nvidia.com/v1"))
    embed_model: str = field(default_factory=lambda: os.getenv("EMBED_MODEL", "nvidia/nemotron-3.5-embed-1b"))
    # NeMo Retriever reranker. Hosted catalog URL by default; for a local NIM use http://localhost:8002/v1/ranking
    rerank_url: str = field(default_factory=lambda: os.getenv(
        "RERANK_URL",
        "https://ai.api.nvidia.com/v1/retrieval/nvidia/nemotron-3.5-rerank-8b/reranking",
    ))
    rerank_model: str = field(default_factory=lambda: os.getenv("RERANK_MODEL", "nvidia/nemotron-3.5-rerank-8b"))

    # Visual GenAI (image generation). Models are tried in order; ones that 404 are skipped.
    image_base_url: str = field(default_factory=lambda: os.getenv("IMAGE_BASE_URL", "https://ai.api.nvidia.com/v1/genai"))
    image_status_url: str = field(default_factory=lambda: os.getenv(
        "IMAGE_STATUS_URL", "https://api.nvcf.nvidia.com/v2/nvcf/pexec/status"))
    image_models: list[str] = field(default_factory=lambda: [m.strip() for m in os.getenv(
        "IMAGE_MODELS",
        "black-forest-labs/flux.2-klein-4b,black-forest-labs/flux.1-schnell,black-forest-labs/flux.1-dev,"
        "stabilityai/stable-diffusion-3-medium").split(",") if m.strip()])

    # ---- Retrieval --------------------------------------------------------
    max_sources: int = field(default_factory=lambda: int(os.getenv("MAX_SOURCES", "8")))
    per_source_limit: int = field(default_factory=lambda: int(os.getenv("PER_SOURCE_LIMIT", "6")))
    chunk_words: int = field(default_factory=lambda: int(os.getenv("CHUNK_WORDS", "180")))
    chunk_overlap: int = field(default_factory=lambda: int(os.getenv("CHUNK_OVERLAP", "40")))
    http_timeout: float = field(default_factory=lambda: float(os.getenv("HTTP_TIMEOUT", "12")))
    use_query_rewrite: bool = field(default_factory=lambda: _bool("USE_QUERY_REWRITE", True))
    use_dense: bool = field(default_factory=lambda: _bool("USE_DENSE", True))
    use_rerank: bool = field(default_factory=lambda: _bool("USE_RERANK", True))

    # ---- Storage ----------------------------------------------------------
    data_dir: Path = field(default_factory=lambda: Path(os.getenv("DATA_DIR", str(BASE_DIR / "data"))))
    contact_email: str = field(default_factory=lambda: os.getenv("CONTACT_EMAIL", "prajna@example.com"))
    cors_origins: list[str] = field(default_factory=lambda: [
        o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()
    ])

    @property
    def nvidia_enabled(self) -> bool:
        """True when we can talk to an NVIDIA endpoint (hosted needs a key; local NIM does not)."""
        local = "localhost" in self.llm_base_url or "127.0.0.1" in self.llm_base_url or "nim-" in self.llm_base_url
        return bool(self.nvidia_api_key) or local

    @property
    def user_agent(self) -> str:
        return f"PrajnaSearch/1.0 (open-source AI search; {self.contact_email})"


settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
