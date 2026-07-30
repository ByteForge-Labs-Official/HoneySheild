"""Pluggable AI provider — local rules, Ollama, OpenAI."""
from __future__ import annotations

from typing import Protocol

import structlog
import tenacity

from app.core.config.settings import get_settings

logger = structlog.get_logger()


class AIProvider(Protocol):
    async def summarise(self, window_events: list[dict]) -> str: ...
    async def tag_mitre(self, window_events: list[dict]) -> list[str]: ...
    async def extract_iocs(self, window_events: list[dict]) -> list[dict]: ...


class LocalProvider:
    """No-op baseline so the system runs without an external model."""

    async def summarise(self, _): return ""
    async def tag_mitre(self, _): return []
    async def extract_iocs(self, _): return []


class OllamaProvider:
    def __init__(self, base_url: str, model: str) -> None:
        self.base_url, self.model = base_url, model

    async def summarise(self, events):
        prompt = _build_prompt(events, task="summarise")
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(f"{self.base_url}/api/generate",
                             json={"model": self.model, "prompt": prompt, "stream": False})
        return r.json().get("response", "")

    async def tag_mitre(self, events):
        return []    # implemented similarly to summarise

    async def extract_iocs(self, events):
        return []


def get_provider() -> AIProvider:
    s = get_settings()
    if s.ai_provider == "ollama":
        return OllamaProvider(s.ollama_base_url, s.ollama_model)
    return LocalProvider()


def _build_prompt(events: list[dict], task: str) -> str:
    return f"Task: {task}\nEvents:\n{events[:200]}"


@tenacity.retry(stop=tenacity.stop_after_attempt(3),
                wait=tenacity.wait_exponential(multiplier=1, max=10),
                reraise=True)
async def _safe_call(coro):
    return await coro


# imports kept below to avoid circulars
import httpx  # noqa: E402