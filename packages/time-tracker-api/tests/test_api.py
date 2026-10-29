"""Testes HTTP com banco SQLite temporario e relogio fixo."""
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from time_tracker_api import create_app
from time_tracker_core import create_sqlite_tracker

TZ = timezone(timedelta(hours=-3))


def _at(h, m=0):
    return datetime(2026, 9, 11, h, m, tzinfo=TZ).isoformat()


@pytest.fixture
def client(tmp_path):
    fixed = datetime(2026, 9, 11, 15, tzinfo=TZ)
    tracker = create_sqlite_tracker(str(tmp_path / "t.db"), clock=lambda: fixed)
    return TestClient(create_app(tracker))


def test_fluxo_completo(client):
    assert client.get("/days/state").json()["status"] == "not_started"
    assert client.post("/days/start", json={"task_id": "T-1", "at": _at(9)}).status_code == 204
    r = client.post("/days/side-task", json={"task_id": "R-1", "minutes": 30, "at": _at(10)})
    assert r.status_code == 204
    r = client.post("/days/pause", json={"at": _at(12), "auto_resume_at": _at(13)})
    assert r.status_code == 200 and r.json()["explicit"] is True
    assert client.get("/days/state").json()["status"] == "paused"
    assert client.post("/days/resume", json={"at": _at(13)}).status_code == 204

    r = client.post("/days/end", json={"at": _at(18)})
    body = r.json()
    assert r.status_code == 200
    # T-1: 3h + 5h = 8h brutas, menos 0,5h da side = 7,5h
    hours = {(t["kind"], t["task_id"]): t["hours"] for t in body["tasks"]}
    assert hours == {("main", "T-1"): 7.5, ("side", "R-1"): 0.5}
    assert body["total_hours"] == 8.0 and body["paused_hours"] == 1.0
    assert client.get("/days/2026-09-11/report").json()["open_day"] is False
    assert client.get("/days/2026-09-11/state").json()["status"] == "ended"


def test_estado_invalido_retorna_409(client):
    r = client.post("/days/pause", json={})
    assert r.status_code == 409 and "detail" in r.json()


def test_validacao_retorna_422(client):
    r = client.post("/days/side-task", json={"task_id": "R", "minutes": 0})
    assert r.status_code == 422


def test_relatorio_sem_eventos_retorna_409(client):
    assert client.get("/days/2026-01-01/report").status_code == 409


def test_historico_listar_e_excluir(client):
    client.post("/days/start", json={"task_id": "T-1", "at": _at(9)})
    client.post("/days/change-task", json={"task_id": "T-2", "at": _at(11)})
    events = client.get("/events").json()
    assert [e["event_type"] for e in events] == ["CHANGE_TASK", "START_DAY"]  # recentes primeiro
    assert client.get("/events", params={"start": "2026-09-12"}).json() == []

    change = events[0]
    assert client.delete(f"/events/{change['id']}").status_code == 204
    assert [e["event_type"] for e in client.get("/events").json()] == ["START_DAY"]
    assert client.get("/days/state").json()["current_task"] == "T-1"
    assert client.delete(f"/events/{change['id']}").status_code == 404
