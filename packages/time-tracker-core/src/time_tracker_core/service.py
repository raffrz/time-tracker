"""Casos de uso do time-tracker.

`TimeTracker` e o unico ponto de entrada para interfaces (CLI, API, ...).
Recebe e devolve tipos de dominio (datetime, timedelta, dataclasses): sem
strings de horario digitadas pelo usuario e sem texto formatado para exibicao.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Callable, Optional

from . import models as m
from .calculator import compute_from_events, derive_state
from .clock import now
from .errors import NotFoundError, TrackerError
from .models import DayReport, DayState, Event, PauseResult
from .repository import EventRepository
from .sqlite_repository import SqliteEventRepository

DEFAULT_AUTO_RESUME = timedelta(hours=24)


class TimeTracker:
    def __init__(
        self, repository: EventRepository, clock: Callable[[], datetime] = now
    ) -> None:
        self._repo = repository
        self._clock = clock

    def today(self) -> date:
        return self._clock().date()

    # ---- consultas ------------------------------------------------------- #
    def get_day_state(self, work_date: Optional[date] = None) -> DayState:
        return derive_state(self._repo.list_for_day(work_date or self.today()))

    def build_report(self, work_date: Optional[date] = None) -> DayReport:
        work_date = work_date or self.today()
        events = self._repo.list_for_day(work_date)
        if not events:
            raise TrackerError(f"Nenhum evento registrado para {work_date}.")
        return compute_from_events(events, work_date, current_time=self._clock())

    def list_events(
        self, start: Optional[date] = None, end: Optional[date] = None
    ) -> list[Event]:
        """Historico de eventos (mais recentes primeiro)."""
        return self._repo.list_events(start, end)

    # ---- comandos -------------------------------------------------------- #
    def start_day(self, task_id: str, at: Optional[datetime] = None) -> None:
        at = at or self._clock()
        wd = at.date()
        state = derive_state(self._repo.list_for_day(wd))
        if state.started and not state.ended:
            raise TrackerError(f"O dia {wd} ja foi iniciado. Finalize-o antes de reinicia-lo.")
        if state.ended:
            raise TrackerError(f"O dia {wd} ja foi finalizado.")
        self._repo.add(wd, Event(m.START_DAY, task_id, at))

    def pause(
        self,
        auto_resume_at: Optional[datetime] = None,
        at: Optional[datetime] = None,
    ) -> PauseResult:
        """Registra uma pausa.

        - `at`: momento em que a pausa comecou (padrao: agora). Permite
          registrar uma pausa retroativa.
        - `auto_resume_at`: retomada prevista (opcional). Sem ela, assume-se
          `at` + 24h e `PauseResult.explicit` e False.
        """
        at = at or self._clock()
        wd = at.date()
        state = derive_state(self._repo.list_for_day(wd))
        if not state.started or state.ended:
            raise TrackerError("Nao ha um dia em andamento para pausar.")
        if state.paused:
            raise TrackerError("O dia ja esta pausado.")
        explicit = auto_resume_at is not None
        resume_at = auto_resume_at if explicit else at + DEFAULT_AUTO_RESUME
        self._repo.add(wd, Event(m.PAUSE, None, at, auto_resume_at=resume_at))
        return PauseResult(auto_resume_at=resume_at, explicit=explicit)

    def resume(self, at: Optional[datetime] = None) -> None:
        at = at or self._clock()
        wd = at.date()
        state = derive_state(self._repo.list_for_day(wd))
        if not state.started or state.ended:
            raise TrackerError("Nao ha um dia em andamento para retomar.")
        if not state.paused:
            raise TrackerError("O dia nao esta pausado.")
        self._repo.add(wd, Event(m.RESUME, None, at))

    def change_task(self, task_id: str, at: Optional[datetime] = None) -> None:
        at = at or self._clock()
        wd = at.date()
        state = derive_state(self._repo.list_for_day(wd))
        if not state.started or state.ended:
            raise TrackerError("Nao ha um dia em andamento para trocar de tarefa.")
        if state.current_task == task_id:
            raise TrackerError(f"A tarefa principal ja e '{task_id}'.")
        self._repo.add(wd, Event(m.CHANGE_TASK, task_id, at))

    def side_task(
        self,
        task_id: str,
        minutes: int,
        description: Optional[str] = None,
        at: Optional[datetime] = None,
    ) -> None:
        at = at or self._clock()
        wd = at.date()
        state = derive_state(self._repo.list_for_day(wd))
        if not state.started or state.ended:
            raise TrackerError("Nao ha um dia em andamento para lancar side-task.")
        if minutes <= 0:
            raise TrackerError("O tempo da side-task deve ser positivo (em minutos).")
        self._repo.add(
            wd,
            Event(m.SIDE_TASK, task_id, at, minutes=minutes, description=description),
        )

    def delete_event(self, event_id: int) -> None:
        """Exclui um evento do historico. O relatorio do dia e recalculado."""
        if not self._repo.delete(event_id):
            raise NotFoundError(f"Evento {event_id} nao encontrado.")

    def end_day(self, at: Optional[datetime] = None) -> DayReport:
        at = at or self._clock()
        wd = at.date()
        state = derive_state(self._repo.list_for_day(wd))
        if not state.started:
            raise TrackerError("Nao ha um dia iniciado para finalizar.")
        if state.ended:
            raise TrackerError("O dia ja foi finalizado.")
        self._repo.add(wd, Event(m.END_DAY, None, at))
        return self.build_report(wd)


def create_sqlite_tracker(
    db_path: str, clock: Callable[[], datetime] = now
) -> TimeTracker:
    """Monta um `TimeTracker` sobre um arquivo SQLite, garantindo o schema."""
    repo = SqliteEventRepository(db_path)
    repo.init_schema()
    return TimeTracker(repo, clock)
