"""Adapter SQLite para `EventRepository` (somente biblioteca padrao).

Datas sao guardadas como texto ISO 8601 (ver schema.sql) e convertidas
explicitamente aqui, entao nao usamos os adapters de tipo do sqlite3.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from importlib import resources
from typing import Iterator, Optional

from .models import Event


def _iso(dt: Optional[datetime]) -> Optional[str]:
    """Serializa datetime -> ISO 8601 (com offset). None passa direto."""
    return dt.isoformat() if dt is not None else None


def _parse_iso(text: Optional[str]) -> Optional[datetime]:
    """Desserializa ISO 8601 -> datetime (aware). None passa direto."""
    return datetime.fromisoformat(text) if text else None


class SqliteEventRepository:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        """Abre e fecha a conexao, com commit/rollback."""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_schema(self) -> None:
        """Aplica o schema.sql (idempotente)."""
        ddl = resources.files(__package__).joinpath("schema.sql").read_text(encoding="utf-8")
        with self._connection() as conn:
            conn.executescript(ddl)

    def add(self, work_date: date, event: Event) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO time_events
                    (work_date, event_type, task_id, occurred_at,
                     auto_resume_at, minutes, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    work_date.isoformat(),
                    event.event_type,
                    event.task_id,
                    _iso(event.occurred_at),
                    _iso(event.auto_resume_at),
                    event.minutes,
                    event.description,
                ),
            )

    _SELECT = """
        SELECT event_type, task_id, occurred_at, auto_resume_at,
               minutes, description, id, work_date
        FROM time_events
    """

    @staticmethod
    def _to_event(r: sqlite3.Row) -> Event:
        return Event(
            event_type=r[0],
            task_id=r[1],
            occurred_at=_parse_iso(r[2]),
            auto_resume_at=_parse_iso(r[3]),
            minutes=r[4],
            description=r[5],
            id=r[6],
            work_date=date.fromisoformat(r[7]),
        )

    def list_for_day(self, work_date: date) -> list[Event]:
        with self._connection() as conn:
            rows = conn.execute(
                self._SELECT + " WHERE work_date = ? ORDER BY occurred_at, id",
                (work_date.isoformat(),),
            ).fetchall()
        return [self._to_event(r) for r in rows]

    def list_events(
        self, start: Optional[date] = None, end: Optional[date] = None
    ) -> list[Event]:
        where, params = [], []
        if start is not None:
            where.append("work_date >= ?")
            params.append(start.isoformat())
        if end is not None:
            where.append("work_date <= ?")
            params.append(end.isoformat())
        clause = (" WHERE " + " AND ".join(where)) if where else ""
        with self._connection() as conn:
            rows = conn.execute(
                self._SELECT + clause + " ORDER BY work_date DESC, occurred_at DESC, id DESC",
                params,
            ).fetchall()
        return [self._to_event(r) for r in rows]

    def delete(self, event_id: int) -> bool:
        with self._connection() as conn:
            cur = conn.execute("DELETE FROM time_events WHERE id = ?", (event_id,))
            return cur.rowcount > 0
