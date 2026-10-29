"""Porta de persistencia do dominio.

O core so conhece esta interface; adapters (SQLite, API remota, memoria...)
a implementam. Isso permite trocar o armazenamento sem tocar nas regras.
"""
from __future__ import annotations

from datetime import date
from typing import Optional, Protocol

from .models import Event


class EventRepository(Protocol):
    def add(self, work_date: date, event: Event) -> None:
        """Persiste um evento do dia `work_date`."""

    def list_for_day(self, work_date: date) -> list[Event]:
        """Eventos do dia, ordenados por `occurred_at` e ordem de insercao."""

    def list_events(
        self, start: Optional[date] = None, end: Optional[date] = None
    ) -> list[Event]:
        """Eventos entre `start` e `end` (inclusivos; None = sem limite), do mais recente ao mais antigo."""

    def delete(self, event_id: int) -> bool:
        """Remove o evento. Retorna False se nao existia."""
