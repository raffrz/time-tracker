"""Configuracao da API.

Banco: TIMETRACKER_DB > `default` do chamador > `~/.time_tracker.db`.
Servidor: TIMETRACKER_API_HOST (127.0.0.1) e TIMETRACKER_API_PORT (8000).
"""
from __future__ import annotations

import os
from typing import Optional


def resolve_db_path(default: Optional[str] = None) -> str:
    path = os.getenv("TIMETRACKER_DB") or default or os.path.join("~", ".time_tracker.db")
    return os.path.expanduser(path)


def resolve_host() -> str:
    return os.getenv("TIMETRACKER_API_HOST", "127.0.0.1")


def resolve_port() -> int:
    return int(os.getenv("TIMETRACKER_API_PORT", "8000"))
