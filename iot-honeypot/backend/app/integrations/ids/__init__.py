"""IDS adapters (Suricata + Zeek) - normalise to Alert dicts."""
from app.integrations.ids.suricata import SuricataClient, parse_suricata_event
from app.integrations.ids.zeek import ZeekTailer, parse_zeek_notice

__all__ = [
    "SuricataClient",
    "parse_suricata_event",
    "ZeekTailer",
    "parse_zeek_notice",
]