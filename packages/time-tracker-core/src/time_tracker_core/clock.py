"""Relogio do dominio."""
from __future__ import annotations

from datetime import date, datetime, timezone


def now() -> datetime:
    """Agora, com timezone local."""
    return datetime.now(timezone.utc).astimezone()


def today() -> date:
    return now().date()
