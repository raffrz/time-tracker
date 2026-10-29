#!/usr/bin/env python3
"""Atalho para subir a API direto do codigo-fonte: `python api.py`.

Usa o banco legado (`time_tracker.db` na raiz) como padrao, igual ao cli.py.
Host/porta: TIMETRACKER_API_HOST (127.0.0.1) e TIMETRACKER_API_PORT (8000).
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
for pkg in ("time-tracker-core", "time-tracker-api"):
    sys.path.insert(0, os.path.join(ROOT, "packages", pkg, "src"))

from time_tracker_api.main import run  # noqa: E402

if __name__ == "__main__":
    run(default_db=os.path.join(ROOT, "time_tracker.db"))
