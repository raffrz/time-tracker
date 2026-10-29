"""Modelos de dominio do time-tracker (sem I/O e sem detalhes de apresentacao)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional

START_DAY = "START_DAY"
PAUSE = "PAUSE"
RESUME = "RESUME"
CHANGE_TASK = "CHANGE_TASK"
SIDE_TASK = "SIDE_TASK"
END_DAY = "END_DAY"


@dataclass
class Event:
    event_type: str
    task_id: Optional[str]
    occurred_at: datetime
    auto_resume_at: Optional[datetime] = None
    minutes: Optional[int] = None
    description: Optional[str] = None
    id: Optional[int] = None            # preenchido pelo repositorio
    work_date: Optional[date] = None    # preenchido pelo repositorio


@dataclass
class DayState:
    started: bool = False
    ended: bool = False
    paused: bool = False
    current_task: Optional[str] = None


@dataclass
class PauseResult:
    """Resultado de `TimeTracker.pause`.

    `explicit` indica se o horario de retomada foi informado pelo chamador
    (True) ou e o padrao de +24h (False).
    """

    auto_resume_at: datetime
    explicit: bool


@dataclass
class DayReport:
    """Horas do dia como duracoes (`timedelta`); formatacao e com a interface."""

    work_date: date
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    main_durations: dict           # task_id -> timedelta (principal, ja liquido de side)
    side_durations: dict           # task_id -> timedelta (side-tasks)
    total_worked: timedelta        # tempo corrido ativo (principal bruto)
    total_paused: timedelta        # soma dos intervalos PAUSE->RESUME
    open_day: bool
