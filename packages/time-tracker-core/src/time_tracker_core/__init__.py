"""time-tracker-core: regras de negocio do controle de tempo por tarefa.

Sem I/O de interface: nenhuma leitura de argv/env, nenhum texto formatado.
Interfaces (CLI, API...) dependem deste pacote, nunca o contrario.
"""
from .calculator import compute_from_events, derive_state
from .clock import now, today
from .errors import NotFoundError, TrackerError
from .models import DayReport, DayState, Event, PauseResult
from .repository import EventRepository
from .service import TimeTracker, create_sqlite_tracker
from .sqlite_repository import SqliteEventRepository

__all__ = [
    "DayReport",
    "DayState",
    "Event",
    "EventRepository",
    "NotFoundError",
    "PauseResult",
    "SqliteEventRepository",
    "TimeTracker",
    "TrackerError",
    "compute_from_events",
    "create_sqlite_tracker",
    "derive_state",
    "now",
    "today",
]
