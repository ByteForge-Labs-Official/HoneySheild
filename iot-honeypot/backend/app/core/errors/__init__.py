"""Error and exception handling."""
from app.core.errors.exceptions import (
    AppError,
    AuthError,
    NotFoundError,
    ConflictError,
    ValidationError,
)
from app.core.errors.handlers import register_exception_handlers

__all__ = [
    "AppError",
    "AuthError",
    "NotFoundError",
    "ConflictError",
    "ValidationError",
    "register_exception_handlers",
]