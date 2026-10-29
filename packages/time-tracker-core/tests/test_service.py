"""Testes dos casos de uso, com repositorio em memoria e relogio fixo."""
from datetime import date, datetime, timedelta, timezone

import pytest

from time_tracker_core import (
    Event,
    TimeTracker,
    TrackerError,
    create_sqlite_tracker,
)

TZ = timezone(timedelta(hours=-3))


def _dt(h, m=0):
    return datetime(2026, 9, 11, h, m, tzinfo=TZ)


class InMemoryRepository:
    def __init__(self):
        self._events: dict[date, list[Event]] = {}

    def add(self, work_date, event):
        self._events.setdefault(work_date, []).append(event)

    def list_for_day(self, work_date):
        return sorted(self._events.get(work_date, []), key=lambda e: e.occurred_at)


@pytest.fixture
def tracker():
    return TimeTracker(InMemoryRepository(), clock=lambda: _dt(15))


def test_pause_sem_retomada_nao_e_explicita(tracker):
    tracker.start_day("TASK-A", at=_dt(9))
    result = tracker.pause()
    assert result.explicit is False
    assert result.auto_resume_at == _dt(15) + timedelta(hours=24)


def test_pause_com_retomada_e_explicita(tracker):
    tracker.start_day("TASK-A", at=_dt(9))
    result = tracker.pause(_dt(23, 59))
    assert result.explicit is True
    assert result.auto_resume_at == _dt(23, 59)


def test_fluxo_completo_gera_relatorio(tracker):
    tracker.start_day("TASK-A", at=_dt(9))
    tracker.pause(at=_dt(12, 39))
    tracker.resume(at=_dt(14, 9))
    report = tracker.end_day(at=_dt(18))
    assert report.main_durations["TASK-A"] == timedelta(hours=7, minutes=30)
    assert report.total_paused == timedelta(hours=1, minutes=30)


def test_estados_invalidos(tracker):
    with pytest.raises(TrackerError):
        tracker.pause()
    tracker.start_day("TASK-A", at=_dt(9))
    with pytest.raises(TrackerError):
        tracker.start_day("TASK-B", at=_dt(10))
    with pytest.raises(TrackerError):
        tracker.resume()
    with pytest.raises(TrackerError):
        tracker.change_task("TASK-A")
    with pytest.raises(TrackerError):
        tracker.side_task("REV", 0)


def test_relatorio_sem_eventos(tracker):
    with pytest.raises(TrackerError):
        tracker.build_report(date(2026, 1, 1))


def test_get_day_state(tracker):
    assert tracker.get_day_state(date(2026, 9, 11)).started is False
    tracker.start_day("TASK-A", at=_dt(9))
    state = tracker.get_day_state()
    assert state.started and not state.paused and state.current_task == "TASK-A"


def test_sqlite_roundtrip(tmp_path):
    tracker = create_sqlite_tracker(str(tmp_path / "t.db"), clock=lambda: _dt(15))
    tracker.start_day("TASK-A", at=_dt(9))
    tracker.side_task("REVIEW-1", 30, "review", at=_dt(10))
    tracker.pause(_dt(13), at=_dt(12))
    tracker.resume(at=_dt(13))
    report = tracker.end_day(at=_dt(18))
    assert report.side_durations["REVIEW-1"] == timedelta(minutes=30)
    assert report.main_durations["TASK-A"] == timedelta(hours=7, minutes=30)
    assert report.total_paused == timedelta(hours=1)
