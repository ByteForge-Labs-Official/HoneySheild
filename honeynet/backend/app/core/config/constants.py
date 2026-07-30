"""Constants for the honeynet backend."""
from __future__ import annotations

from enum import StrEnum


class Protocol(StrEnum):
    SSH    = "ssh"
    TELNET = "telnet"
    HTTP   = "http"
    RTSP   = "rtsp"
    MQTT   = "mqtt"
    MODBUS = "modbus"
    UPNP   = "upnp"


class Severity(StrEnum):
    INFO     = "info"
    LOW      = "low"
    MEDIUM   = "medium"
    HIGH     = "high"
    CRITICAL = "critical"


# Bounded sizes — every attacker-derived string is sanitized to these limits
MAX_LINE_LEN  = 1024
MAX_VALUE_LEN = 4096
MAX_TAGS      = 32

# Redis stream keys
RAW_ATTACKS_STREAM = "attacks:raw"
LIVE_ATTACKS_PUBSUB = "attacks:live"

# Celery queues
QUEUE_DEFAULT = "default"
QUEUE_INGEST  = "ingest"
QUEUE_ANALYZE = "analyze"
