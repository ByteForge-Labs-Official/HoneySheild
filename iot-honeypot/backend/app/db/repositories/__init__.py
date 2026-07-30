"""Repository layer (thin wrappers over the session for testability)."""
from app.db.repositories.user_repository import UserRepository
from app.db.repositories.honeypot_repository import HoneypotRepository, HoneypotEventRepository
from app.db.repositories.alert_repository import AlertRepository
from app.db.repositories.ai_repository import AIInsightRepository

__all__ = [
    "UserRepository",
    "HoneypotRepository",
    "HoneypotEventRepository",
    "AlertRepository",
    "AIInsightRepository",
]