#!/usr/bin/env python3
"""Atalho de compatibilidade: `python cli.py ...` (usado pelo alias do bashrc).

Roda direto do codigo-fonte do monorepo, sem precisar instalar os pacotes, e
mantem o banco legado (`time_tracker.db` na raiz) como padrao.
Para instalar de verdade: `pip install -e packages/time-tracker-core -e packages/time-tracker-cli`.
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
for pkg in ("time-tracker-core", "time-tracker-cli"):
    sys.path.insert(0, os.path.join(ROOT, "packages", pkg, "src"))

from time_tracker_cli.main import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(default_db=os.path.join(ROOT, "time_tracker.db")))
