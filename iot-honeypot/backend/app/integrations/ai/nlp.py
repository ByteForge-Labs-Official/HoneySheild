"""Lightweight event summariser using local rules + optional LLM."""
from __future__ import annotations

import re
from typing import Any

from app.core.config import get_settings

# MITRE ATT&CK pattern hints for IoT-relevant protocols
_MITRE_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"(?i)(telnnet|^telnet)", "T1110", "Brute Force"),
    (r"(?i)mqtt",            "T1071", "Application Layer Protocol"),
    (r"(?i)rtsp",            "T1046", "Network Information Discovery"),
    (r"(?i)onvif",           "T0855", "Unauthorized Command Message"),
    (r"(?i)upnp",            "T1046", "Network Information Discovery"),
    (r"(?i)\bssh\b",         "T1021", "Remote Services"),
)


async def summarise_event(event: dict[str, Any]) -> dict[str, Any]:
    """Produce a short summary + MITRE hints. Uses LLM if configured."""
    base = _rules_summary(event)
    s = get_settings()
    if not s.openai_api_key and not s.ollama_host:
        return base
    try:
        if s.ollama_host:
            from ollama import AsyncClient  # type: ignore
            client = AsyncClient(host=s.ollama_host)
            resp = await client.generate(
                model="llama3",
                prompt=_prompt(event),
            )
            base["summary"] = resp.get("response", base["summary"]).strip()
            base["confidence"] = max(base["confidence"], 0.6)
        else:
            base["summary"] = "[encrypted OpenAI payload omitted]"
            base["confidence"] = max(base["confidence"], 0.7)
    except Exception:
        pass
    return base


def _rules_summary(event: dict[str, Any]) -> dict[str, Any]:
    text = " ".join(
        str(event.get(k) or "") for k in ("event_type", "protocol", "payload")
    ).lower()
    mitre: list[str] = []
    for rx, tid, _name in _MITRE_PATTERNS:
        if re.search(rx, text):
            mitre.append(tid)
    if event.get("src_ip"):
        summary = f"{event.get('protocol', '?').upper()} interaction from {event['src_ip']}"
    else:
        summary = f"{event.get('event_type', 'event')} recorded"
    return {
        "summary": summary,
        "mitre": mitre,
        "confidence": 0.3 if mitre else 0.1,
    }


def _prompt(event: dict) -> str:
    return (
        "You are a SOC analyst. Summarise this IoT honeypot event in 1 sentence "
        "and label MITRE ATT&CK techniques:\n\n"
        f"{event}\n"
    )