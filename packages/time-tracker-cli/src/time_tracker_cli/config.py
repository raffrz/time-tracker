"""Configuracao da CLI: onde fica o banco SQLite.

Ordem de resolucao: variavel TIMETRACKER_DB (inclusive via .env, se
python-dotenv estiver instalado) > `default` informado pelo chamador >
`~/.time_tracker.db`.
"""
from __future__ import annotations

import os
from typing import Optional

try:  # carrega .env automaticamente se disponivel (opcional)
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover - dotenv e opcional
    pass

FALLBACK_DB = os.path.join("~", ".time_tracker.db")


def resolve_db_path(default: Optional[str] = None) -> str:
    env_path = os.getenv("TIMETRACKER_DB")
    return os.path.expanduser(env_path or default or FALLBACK_DB)
