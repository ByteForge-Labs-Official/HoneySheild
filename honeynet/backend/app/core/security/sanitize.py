"""Input sanitisation utilities — the JVM Sanitizer equivalent."""
from __future__ import annotations

import re

from app.core.config.constants import MAX_LINE_LEN, MAX_VALUE_LEN

# Strip ANSI / CSI / OSC escape sequences, plus C0/C1 controls.
_ANSI_RE = re.compile(
    r"\x1b\][^\x07\x1b]*?(?:\x07|\x1b\\)"   # OSC
    r"|\x1b\[[0-?]*[ -/]*[@-~]"              # CSI
    r"|\x1b[\(\)][0-9A-Za-z]"                # charset
)
_CTRL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_TRAVERSAL_RE = re.compile(r"\.\./|\.\.\x5c|%2e%2e[/\\%]", re.IGNORECASE)


def strip_control_chars(value: str) -> str:
    return _CTRL_RE.sub("", value)


def strip_ansi(value: str) -> str:
    return _ANSI_RE.sub("", value)


def strip_path_traversal(value: str) -> str:
    return _TRAVERSAL_RE.sub("", value)


def clean_line(raw: str | None, *, cap: int = MAX_LINE_LEN) -> str:
    """Sanitize a single line of attacker input — caller knows it ends in \\n."""
    if not raw:
        return ""
    s = strip_ansi(raw)
    s = strip_control_chars(s)
    s = strip_path_traversal(s)
    return s[:cap].rstrip("\r\n")


def clean_value(raw: str | None, *, cap: int = MAX_VALUE_LEN) -> str:
    if not raw:
        return ""
    s = strip_ansi(raw)
    s = strip_control_chars(s)
    return s[:cap]
