"""Contratos HTTP (entrada/saida) e conversao de/para tipos do core."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional

from pydantic import BaseModel, Field

from time_tracker_core import DayReport, DayState, Event, PauseResult


class _AtMixin(BaseModel):
    at: Optional[datetime] = Field(
        None, description="Momento do evento (ISO 8601). Sem fuso = fuso local. Padrao: agora."
    )


class StartDayIn(_AtMixin):
    task_id: str = Field(min_length=1)


class PauseIn(_AtMixin):
    auto_resume_at: Optional[datetime] = Field(None, description="Retomada prevista (opcional).")


class ResumeIn(_AtMixin):
    pass


class ChangeTaskIn(_AtMixin):
    task_id: str = Field(min_length=1)


class SideTaskIn(_AtMixin):
    task_id: str = Field(min_length=1)
    minutes: int = Field(gt=0)
    description: Optional[str] = None


class EndDayIn(_AtMixin):
    pass


class PauseOut(BaseModel):
    auto_resume_at: datetime
    explicit: bool

    @classmethod
    def from_core(cls, r: PauseResult) -> "PauseOut":
        return cls(auto_resume_at=r.auto_resume_at, explicit=r.explicit)


class DayStateOut(BaseModel):
    work_date: date
    status: str = Field(description="not_started | in_progress | paused | ended")
    current_task: Optional[str]

    @classmethod
    def from_core(cls, work_date: date, s: DayState) -> "DayStateOut":
        if not s.started:
            status = "not_started"
        elif s.ended:
            status = "ended"
        elif s.paused:
            status = "paused"
        else:
            status = "in_progress"
        return cls(work_date=work_date, status=status, current_task=s.current_task)


class TaskTimeOut(BaseModel):
    kind: str = Field(description="main | side")
    task_id: str
    seconds: int
    hours: float


class ReportOut(BaseModel):
    work_date: date
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    open_day: bool
    tasks: list[TaskTimeOut]
    total_seconds: int
    total_hours: float
    paused_seconds: int
    paused_hours: float

    @classmethod
    def from_core(cls, r: DayReport) -> "ReportOut":
        def item(kind: str, task_id: str, d: timedelta) -> TaskTimeOut:
            return TaskTimeOut(
                kind=kind, task_id=task_id, seconds=int(d.total_seconds()), hours=_hours(d)
            )

        tasks = [item("main", t, d) for t, d in sorted(r.main_durations.items())]
        tasks += [item("side", t, d) for t, d in sorted(r.side_durations.items())]
        total = sum(r.main_durations.values(), timedelta()) + sum(
            r.side_durations.values(), timedelta()
        )
        return cls(
            work_date=r.work_date,
            started_at=r.started_at,
            ended_at=r.ended_at,
            open_day=r.open_day,
            tasks=tasks,
            total_seconds=int(total.total_seconds()),
            total_hours=_hours(total),
            paused_seconds=int(r.total_paused.total_seconds()),
            paused_hours=_hours(r.total_paused),
        )


class EventOut(BaseModel):
    id: int
    work_date: date
    event_type: str
    task_id: Optional[str]
    occurred_at: datetime
    auto_resume_at: Optional[datetime]
    minutes: Optional[int]
    description: Optional[str]

    @classmethod
    def from_core(cls, e: Event) -> "EventOut":
        return cls(
            id=e.id,
            work_date=e.work_date,
            event_type=e.event_type,
            task_id=e.task_id,
            occurred_at=e.occurred_at,
            auto_resume_at=e.auto_resume_at,
            minutes=e.minutes,
            description=e.description,
        )


def _hours(d: timedelta) -> float:
    return round(d.total_seconds() / 3600, 2)


def localize(dt: Optional[datetime]) -> Optional[datetime]:
    """Datetime sem fuso e interpretado como horario local."""
    return dt.astimezone() if dt is not None and dt.tzinfo is None else dt
