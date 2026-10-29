"""Ponto de entrada: monta o app sobre SQLite e sobe o uvicorn."""
from __future__ import annotations

from typing import Optional

import uvicorn
from fastapi import FastAPI

from time_tracker_core import create_sqlite_tracker

from .app import create_app
from .config import resolve_db_path, resolve_host, resolve_port


def build_app(default_db: Optional[str] = None) -> FastAPI:
    return create_app(create_sqlite_tracker(resolve_db_path(default_db)))


def run(default_db: Optional[str] = None) -> None:
    uvicorn.run(build_app(default_db), host=resolve_host(), port=resolve_port())


if __name__ == "__main__":
    run()
