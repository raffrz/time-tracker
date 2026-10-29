"""Calculo puro de estado e horas a partir da sequencia de eventos.

O dia de trabalho e uma sequencia de eventos (ver schema.sql). As horas sao
derivadas dessa sequencia:

- A "task principal" e a tarefa vigente definida por START_DAY e alterada por
  CHANGE_TASK.
- O cronometro corre do START_DAY ao END_DAY (ou "agora", se o dia ainda esta
  aberto), descontando os intervalos entre PAUSE e RESUME.
- Cada intervalo ativo e creditado a task principal vigente naquele intervalo.
- SIDE_TASK lanca minutos manualmente numa tarefa paralela; esse tempo e
  debitado da task principal vigente no momento do lancamento e creditado a
  side-task. Assim o somatorio do dia continua fechando com o tempo corrido.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Optional

from . import models as m
from .clock import now
from .models import DayReport, DayState, Event


def derive_state(events: list[Event]) -> DayState:
    state = DayState()
    for ev in events:
        if ev.event_type == m.START_DAY:
            state.started = True
            state.current_task = ev.task_id
        elif ev.event_type == m.PAUSE:
            state.paused = True
        elif ev.event_type == m.RESUME:
            state.paused = False
        elif ev.event_type == m.CHANGE_TASK:
            state.current_task = ev.task_id
        elif ev.event_type == m.END_DAY:
            state.ended = True
    return state


def compute_from_events(
    events: list[Event], work_date: date, current_time: Optional[datetime] = None
) -> DayReport:
    """Calculo puro a partir de uma lista de eventos ordenada por tempo.

    `current_time` permite testar dias em aberto de forma deterministica; se
    None, usa now().
    """
    current_time = current_time or now()

    started_at = None
    ended_at = None
    current_task = None
    paused = False
    last_ts: Optional[datetime] = None

    main_gross: dict = defaultdict(timedelta)   # tempo corrido por task principal
    side_durations: dict = defaultdict(timedelta)
    side_by_task_context: dict = defaultdict(timedelta)  # side lancado enquanto task X era principal
    total_paused = timedelta()
    pause_started_at: Optional[datetime] = None  # inicio da pausa vigente (se pausado)

    def accrue(until: datetime):
        nonlocal last_ts
        if last_ts is not None and current_task is not None and not paused:
            delta = until - last_ts
            if delta.total_seconds() > 0:
                main_gross[current_task] += delta
        last_ts = until

    open_day = True
    for ev in events:
        if ev.event_type == m.START_DAY:
            started_at = ev.occurred_at
            current_task = ev.task_id
            last_ts = ev.occurred_at
        elif ev.event_type == m.PAUSE:
            accrue(ev.occurred_at)
            paused = True
            pause_started_at = ev.occurred_at
        elif ev.event_type == m.RESUME:
            paused = False
            if pause_started_at is not None:
                delta = ev.occurred_at - pause_started_at
                if delta.total_seconds() > 0:
                    total_paused += delta
                pause_started_at = None
            last_ts = ev.occurred_at
        elif ev.event_type == m.CHANGE_TASK:
            accrue(ev.occurred_at)
            current_task = ev.task_id
        elif ev.event_type == m.SIDE_TASK:
            accrue(ev.occurred_at)
            dur = timedelta(minutes=ev.minutes or 0)
            side_durations[ev.task_id] += dur
            # debita a side da task principal vigente no momento do lancamento
            if current_task is not None:
                side_by_task_context[current_task] += dur
        elif ev.event_type == m.END_DAY:
            accrue(ev.occurred_at)
            ended_at = ev.occurred_at
            open_day = False

    # Se o dia ainda esta aberto, contabiliza ate agora (se nao estiver pausado).
    if open_day:
        accrue(current_time)
        # pausa ainda em aberto: conta ate agora
        if paused and pause_started_at is not None:
            delta = current_time - pause_started_at
            if delta.total_seconds() > 0:
                total_paused += delta

    # Liquida: principal = bruto - side lancado sob aquela principal (nunca negativo).
    main_net: dict = {}
    for task_id, gross in main_gross.items():
        debit = side_by_task_context.get(task_id, timedelta())
        net = gross - debit
        if net.total_seconds() < 0:
            net = timedelta()
        main_net[task_id] = net

    total_worked = sum(main_gross.values(), timedelta())

    return DayReport(
        work_date=work_date,
        started_at=started_at,
        ended_at=ended_at,
        main_durations=main_net,
        side_durations=dict(side_durations),
        total_worked=total_worked,
        total_paused=total_paused,
        open_day=open_day,
    )
