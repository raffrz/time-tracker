"""Testes dos parsers de entrada e da formatacao de saida da CLI."""
from datetime import date, datetime, timedelta, timezone

import pytest

from time_tracker_cli.formatting import format_hours_decimal, render_report
from time_tracker_cli.parsing import (
    parse_auto_resume_at,
    parse_date,
    parse_start_time,
    parse_time_spent,
)
from time_tracker_core import DayReport

TZ = timezone(timedelta(hours=-3))


def _dt(h, m=0):
    return datetime(2026, 9, 11, h, m, tzinfo=TZ)


def test_format_hours_decimal():
    assert format_hours_decimal(timedelta(hours=7, minutes=30)) == "7,50"
    assert format_hours_decimal(timedelta(hours=8)) == "8,00"
    assert format_hours_decimal(timedelta(minutes=45)) == "0,75"


def test_parse_time_spent():
    assert parse_time_spent("90") == 90
    assert parse_time_spent("1h30") == 90
    assert parse_time_spent("1h30m") == 90
    assert parse_time_spent("1:30") == 90
    assert parse_time_spent("45m") == 45
    assert parse_time_spent("2h") == 120


def test_parse_start_time():
    ref = _dt(14, 30)
    assert parse_start_time(None, ref) == ref
    assert parse_start_time("09:00", ref) == _dt(9, 0)
    assert parse_start_time("2026-09-11 08:15", ref) == _dt(8, 15)
    assert parse_start_time("2026-09-11T08:15", ref) == _dt(8, 15)
    with pytest.raises(ValueError):
        parse_start_time("abc", ref)


def test_parse_date():
    ref = date(2026, 9, 22)
    assert parse_date(None, ref) == ref
    assert parse_date("2026-09-11", ref) == date(2026, 9, 11)
    with pytest.raises(ValueError):
        parse_date("11/09/2026", ref)


def test_parse_auto_resume_at():
    ref = _dt(14, 30)
    assert parse_auto_resume_at(None, ref) is None
    assert parse_auto_resume_at("23:59", ref) == _dt(23, 59)
    # horario que ja passou -> amanha
    assert parse_auto_resume_at("09:00", ref) == _dt(9, 0) + timedelta(days=1)
    assert parse_auto_resume_at("2026-09-12 08:00", ref) == datetime(2026, 9, 12, 8, 0, tzinfo=TZ)
    with pytest.raises(ValueError):
        parse_auto_resume_at("xx", ref)


def test_render_report():
    report = DayReport(
        work_date=date(2026, 9, 11),
        started_at=_dt(9),
        ended_at=_dt(18),
        main_durations={"TASK-123": timedelta(hours=7, minutes=15)},
        side_durations={"REVIEW-1": timedelta(minutes=45)},
        total_worked=timedelta(hours=8),
        total_paused=timedelta(hours=1),
        open_day=False,
    )
    text = render_report(report)
    assert "Relatorio do dia 2026-09-11" in text
    assert "principal  TASK-123" in text and "7,25" in text
    assert "side-task  REVIEW-1" in text and "0,75" in text
    assert text.splitlines()[-2].strip().endswith("8,00")  # TOTAL
    assert text.splitlines()[-1].strip().endswith("1,00")  # Pausas
