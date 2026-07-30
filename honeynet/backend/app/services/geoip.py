"""GeoIP enrichment — MaxMind DB lookup with graceful fallback."""
from __future__ import annotations

import ipaddress
from functools import lru_cache

import geoip2.database
import structlog

logger = structlog.get_logger()
_DB_PATH = "/usr/share/GeoIP/GeoLite2-Country.mmdb"
_reader: geoip2.database.Reader | None = None


def _get_reader() -> geoip2.database.Reader | None:
    global _reader
    if _reader is None:
        try:
            _reader = geoip2.database.Reader(_DB_PATH)
        except FileNotFoundError:
            logger.warning("geoip.db.missing", path=_DB_PATH)
    return _reader


async def enrich_ip(ip: str) -> dict:
    """Return {country_iso, asn}.  Returns empty dict on lookup failure."""
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        return {}

    rdr = _get_reader()
    if rdr is None:
        return {}

    try:
        resp = rdr.country(ip)
    except (geoip2.errors.AddressNotFoundError, ValueError):
        return {}
    return {"country_iso": resp.country.iso_code}


@lru_cache(maxsize=512)
async def country_meta(iso: str) -> dict | None:
    """Cheap static lookup table — extend with a real dataset."""
    return _COUNTRY_META.get(iso.upper())


_COUNTRY_META = {
    "US": {"name": "United States", "lat":  37.0902, "lon": -95.7129},
    "DE": {"name": "Germany",       "lat":  51.1657, "lon":  10.4515},
    "RU": {"name": "Russian Federation", "lat": 61.5240, "lon": 105.3188},
    "CN": {"name": "China",         "lat":  35.8617, "lon": 104.1954},
    "FR": {"name": "France",        "lat":  46.2276, "lon":   2.2137},
    "BR": {"name": "Brazil",        "lat": -14.2350, "lon": -51.9253},
    "IN": {"name": "India",         "lat":  20.5937, "lon":  78.9629},
    "GB": {"name": "United Kingdom","lat":  55.3781, "lon":  -3.4360},
    "JP": {"name": "Japan",         "lat":  36.2048, "lon": 138.2529},
    "AU": {"name": "Australia",     "lat": -25.2744, "lon": 133.7751},
}