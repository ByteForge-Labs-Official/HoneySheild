"""AI enrichment metrics.

Used by ``app.integrations.ai`` to record provider outcomes.  Never
include raw prompt/response text in labels.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Iterator

from app.core.monitoring.metrics import (
    honeynet_ai_insights_total,
    honeynet_ai_request_duration_seconds,
    honeynet_ai_tokens_total,
)


def init() -> None:
    honeynet_ai_insights_total.labels(provider="-", status="-").inc(0)


def observe(provider: str, status: str) -> None:
    honeynet_ai_insights_total.labels(provider=provider, status=status).inc()


@contextmanager
def time_request(provider: str) -> Iterator[dict]:
    """Wrap an upstream AI call.

    Yields a dict the caller can populate with ``prompt_tokens`` /
    ``completion_tokens`` to feed the tokens counter.
    """
    start = time.perf_counter()
    state: dict = {"prompt_tokens": 0, "completion_tokens": 0}
    try:
        yield state
    finally:
        honeynet_ai_request_duration_seconds.labels(provider=provider).observe(
            time.perf_counter() - start
        )
        if state["prompt_tokens"]:
            honeynet_ai_tokens_total.labels(provider=provider, kind="prompt").inc(
                state["prompt_tokens"]
            )
        if state["completion_tokens"]:
            honeynet_ai_tokens_total.labels(provider=provider, kind="completion").inc(
                state["completion_tokens"]
            )


def record_tokens(provider: str, prompt: int, completion: int) -> None:
    if prompt:
        honeynet_ai_tokens_total.labels(provider=provider, kind="prompt").inc(prompt)
    if completion:
        honeynet_ai_tokens_total.labels(provider=provider, kind="completion").inc(completion)
