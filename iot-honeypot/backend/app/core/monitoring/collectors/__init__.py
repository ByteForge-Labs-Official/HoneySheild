"""Custom application-side Prometheus collectors.

Each sub-module owns a single concern and exposes a tiny API:
``init()`` to wire gauges/counters and a handful of helper functions to
emit observations from other parts of the codebase.

Importing these sub-modules is intentionally cheap and side-effect-free
until ``init()`` is called — the FastAPI factory in
``app.core.monitoring.install`` is the single bootstrapper.
"""
