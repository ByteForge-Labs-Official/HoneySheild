"""ORM models — re-exported so Alembic sees the full metadata.

The model files are grouped by domain, one domain per file. Each file
documents the table(s) it owns and the relationships to the others.
"""
from app.db.models.ai import AIInsight
from app.db.models.audit_logs import AuditLog
from app.db.models.base import TimestampMixin, UUIDPKMixin
from app.db.models.devices import Device, Service
from app.db.models.events import Event, Log
from app.db.models.honeypot import Honeypot, HoneypotEvent
from app.db.models.ids import Alert
from app.db.models.indicators_of_compromise import (
    IOC,
    IOCMalwareLink,
    IOCThreatIntelLink,
)
from app.db.models.network_assets import NetworkAsset, NetworkAssetRelationship
from app.db.models.notifications import Notification
from app.db.models.rbac import Permission, Role, RolePermission, UserRole
from app.db.models.reports import Report
from app.db.models.sessions import Session
from app.db.models.settings import Setting
from app.db.models.threat_intel import MalwareMetadata, ThreatIntel
from app.db.models.user import User

__all__ = [
    # mixins
    "TimestampMixin",
    "UUIDPKMixin",
    # identity & access
    "User",
    "Role",
    "Permission",
    "UserRole",
    "RolePermission",
    # inventory
    "Honeypot",
    "HoneypotEvent",
    "Device",
    "Service",
    "NetworkAsset",
    "NetworkAssetRelationship",
    # telemetry
    "Event",
    "Log",
    "Session",
    # detection
    "Alert",
    "AIInsight",
    # intel & iocs
    "ThreatIntel",
    "MalwareMetadata",
    "IOC",
    "IOCThreatIntelLink",
    "IOCMalwareLink",
    # reporting & outbound
    "Report",
    "Notification",
    "AuditLog",
    "Setting",
]