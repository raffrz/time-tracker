"""Testes do calculo puro de horas (sem DB)."""
from datetime import datetime, timedelta, timezone

from time_tracker_core import Event, compute_from_events

TZ = timezone(timedelta(hours=-3))


def _dt(h, m=0):
    return datetime(2026, 9, 11, h, m, tzinfo=TZ)


def _hours(td):
    return round(td.total_seconds() / 3600, 2)


def test_full_day_with_pause_change_and_side():
    wd = _dt(9).date()
    events = [
        Event("START_DAY", "TASK-A", _dt(9, 0)),
        Event("SIDE_TASK", "REVIEW-1", _dt(10, 0), minutes=30, description="review"),
        Event("PAUSE", None, _dt(12, 0)),
        Event("RESUME", None, _dt(13, 0)),
        Event("CHANGE_TASK", "TASK-B", _dt(15, 0)),
        Event("END_DAY", None, _dt(18, 0)),
    ]
    report = compute_from_events(events, wd)

    # Bruto: TASK-A = 09-12 (3h) + 13-15 (2h) = 5h; TASK-B = 15-18 = 3h
    # Side REVIEW-1 = 30m debitado da principal vigente as 10:00 (TASK-A)
    # => TASK-A liquido = 4,5h
    assert _hours(report.main_durations["TASK-A"]) == 4.5
    assert _hours(report.main_durations["TASK-B"]) == 3.0
    assert _hours(report.side_durations["REVIEW-1"]) == 0.5

    total = sum(report.main_durations.values(), timedelta()) + sum(
        report.side_durations.values(), timedelta()
    )
    assert _hours(total) == 8.0


def test_open_day_uses_current_time():
    events = [Event("START_DAY", "TASK-A", _dt(9, 0))]
    report = compute_from_events(events, _dt(9).date(), current_time=_dt(11, 30))
    assert report.open_day is True
    assert _hours(report.main_durations["TASK-A"]) == 2.5


def test_pause_open_day_does_not_accrue_while_paused():
    events = [
        Event("START_DAY", "TASK-A", _dt(9, 0)),
        Event("PAUSE", None, _dt(10, 0)),
    ]
    # ainda pausado as 15:00 -> so contam 09-10 = 1h
    report = compute_from_events(events, _dt(9).date(), current_time=_dt(15, 0))
    assert _hours(report.main_durations["TASK-A"]) == 1.0


def test_almoco_retroativo_desconta_intervalo():
    # Dia 09:00, almoco 12:39->14:09 (1h30), fim 18:00 => 9h - 1h30 = 7h30.
    events = [
        Event("START_DAY", "TASK-A", _dt(9, 0)),
        Event("PAUSE", None, _dt(12, 39)),
        Event("RESUME", None, _dt(14, 9)),
        Event("END_DAY", None, _dt(18, 0)),
    ]
    report = compute_from_events(events, _dt(9).date())
    assert _hours(report.main_durations["TASK-A"]) == 7.5


def test_total_paused_soma_intervalos():
    events = [
        Event("START_DAY", "TASK-A", _dt(9, 0)),
        Event("PAUSE", None, _dt(12, 39)),
        Event("RESUME", None, _dt(14, 9)),   # 1h30
        Event("PAUSE", None, _dt(16, 0)),
        Event("RESUME", None, _dt(16, 15)),  # 15m
        Event("END_DAY", None, _dt(18, 0)),
    ]
    report = compute_from_events(events, _dt(9).date())
    assert _hours(report.total_paused) == 1.75


def test_total_paused_pausa_em_aberto():
    events = [
        Event("START_DAY", "TASK-A", _dt(9, 0)),
        Event("PAUSE", None, _dt(12, 0)),
    ]
    report = compute_from_events(events, _dt(9).date(), current_time=_dt(13, 30))
    assert _hours(report.total_paused) == 1.5
