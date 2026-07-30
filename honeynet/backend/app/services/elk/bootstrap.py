"""ELK bootstrap — creates ILM policy + index template for honeypot logs."""
from __future__ import annotations

import httpx

from app.core.config.settings import get_settings


async def create_ilm_policy(name: str = "honeypot-ilm") -> None:
    s = get_settings()
    url = f"http://elasticsearch:9200/_ilm/policy/{name}"
    policy = {
        "policy": {
            "phases": {
                "hot":  {"actions": {"rollover": {"max_age": "1d", "max_size": "10gb"}}},
                "warm": {"min_age": "7d", "actions": {"shrink": {"number_of_shards": 1}}},
                "cold": {"min_age": "30d", "actions": {"freeze": {}}},
                "delete": {"min_age": "90d", "actions": {"delete": {}}},
            }
        }
    }
    async with httpx.AsyncClient(timeout=10) as c:
        await c.put(url, json=policy)


async def create_index_template(name: str = "honeypot-evt") -> None:
    url = "http://elasticsearch:9200/_index_template/" + name
    template = {
        "index_patterns": ["honeypot-*"],
        "template": {
            "settings": {
                "number_of_shards": 2,
                "number_of_replicas": 1,
                "index.lifecycle.name": "honeypot-ilm",
            },
            "mappings": {
                "properties": {
                    "@timestamp":  {"type": "date"},
                    "src_ip":      {"type": "ip"},
                    "dst_port":    {"type": "integer"},
                    "protocol":    {"type": "keyword"},
                    "severity":    {"type": "keyword"},
                    "kind":        {"type": "keyword"},
                    "raw":         {"type": "text"},
                    "mitre_tags":  {"type": "keyword"},
                }
            },
        },
    }
    async with httpx.AsyncClient(timeout=10) as c:
        await c.put(url, json=template)