"""Aplicacao FastAPI. So HTTP/serializacao; regras ficam no core."""
from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from time_tracker_core import NotFoundError, TimeTracker, TrackerError

from . import schemas as s


def create_app(tracker: TimeTracker) -> FastAPI:
    app = FastAPI(title="time-tracker API", version="0.1.0")

    @app.exception_handler(TrackerError)
    async def _tracker_error(_: Request, exc: TrackerError) -> JSONResponse:
        # Estado invalido para a operacao (ex.: dia ja iniciado) -> conflito.
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(NotFoundError)
    async def _not_found(_: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    # ---- comandos (no instante `at`, padrao: agora) ---------------------- #
    @app.post("/days/start", status_code=204)
    def start_day(body: s.StartDayIn) -> Response:
        tracker.start_day(body.task_id, at=s.localize(body.at))
        return Response(status_code=204)

    @app.post("/days/pause", response_model=s.PauseOut)
    def pause(body: s.PauseIn) -> s.PauseOut:
        result = tracker.pause(s.localize(body.auto_resume_at), at=s.localize(body.at))
        return s.PauseOut.from_core(result)

    @app.post("/days/resume", status_code=204)
    def resume(body: s.ResumeIn) -> Response:
        tracker.resume(at=s.localize(body.at))
        return Response(status_code=204)

    @app.post("/days/change-task", status_code=204)
    def change_task(body: s.ChangeTaskIn) -> Response:
        tracker.change_task(body.task_id, at=s.localize(body.at))
        return Response(status_code=204)

    @app.post("/days/side-task", status_code=204)
    def side_task(body: s.SideTaskIn) -> Response:
        tracker.side_task(
            body.task_id, body.minutes, body.description, at=s.localize(body.at)
        )
        return Response(status_code=204)

    @app.post("/days/end", response_model=s.ReportOut)
    def end_day(body: s.EndDayIn) -> s.ReportOut:
        return s.ReportOut.from_core(tracker.end_day(at=s.localize(body.at)))

    # ---- consultas (rotas fixas antes das parametrizadas) ----------------- #
    @app.get("/days/state", response_model=s.DayStateOut)
    def state_today() -> s.DayStateOut:
        wd = tracker.today()
        return s.DayStateOut.from_core(wd, tracker.get_day_state(wd))

    @app.get("/days/report", response_model=s.ReportOut)
    def report_today() -> s.ReportOut:
        return s.ReportOut.from_core(tracker.build_report(tracker.today()))

    @app.get("/days/{work_date}/state", response_model=s.DayStateOut)
    def state(work_date: date) -> s.DayStateOut:
        return s.DayStateOut.from_core(work_date, tracker.get_day_state(work_date))

    @app.get("/days/{work_date}/report", response_model=s.ReportOut)
    def report(work_date: date) -> s.ReportOut:
        return s.ReportOut.from_core(tracker.build_report(work_date))

    # ---- historico -------------------------------------------------------- #
    @app.get("/events", response_model=list[s.EventOut])
    def list_events(
        start: Optional[date] = None, end: Optional[date] = None
    ) -> list[s.EventOut]:
        return [s.EventOut.from_core(e) for e in tracker.list_events(start, end)]

    @app.delete("/events/{event_id}", status_code=204)
    def delete_event(event_id: int) -> Response:
        tracker.delete_event(event_id)
        return Response(status_code=204)

    return app
