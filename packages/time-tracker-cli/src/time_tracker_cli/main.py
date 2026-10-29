"""Time-tracker CLI: controle de tempo gasto por tarefa.

Comandos:
  --start-day TASK_ID [START_TIME]  Inicia o dia com a tarefa principal.
                               START_TIME opcional HH:MM ou 'YYYY-MM-DD HH:MM'
                               (padrao: agora).
  --pause [HH:MM]              Pausa o cronometro. Horario de retomada opcional
                               (HH:MM ou 'YYYY-MM-DD HH:MM'). Sem valor, nenhuma
                               retomada automatica e anunciada.
  --pause-at HH:MM             Horario retroativo de inicio da pausa (use junto
                               com --pause). Padrao: agora.
  --resume                     Retoma apos uma pausa.
  --resume-at HH:MM            Horario retroativo da retomada (use junto com
                               --resume). Padrao: agora.
  --side-task TASK_ID TIME DESC  Lanca tempo numa tarefa paralela
                               (ex: code review, reuniao). TIME: 90, 1h30, 1:30.
  --change-task TASK_ID        Troca a tarefa principal sem encerrar o dia.
  --end-day                    Finaliza o dia e imprime a tabela de horas.
  --report [DATE]             Mostra a tabela de um dia (padrao: hoje), sem
                               finalizar. DATE opcional no formato YYYY-MM-DD.
  --status                     Mostra o estado atual do dia.
  --init                       Cria/atualiza o schema no banco.

Banco: arquivo SQLite local (caminho configuravel via TIMETRACKER_DB).
"""
from __future__ import annotations

import argparse
import sys
from typing import Optional

from time_tracker_core import SqliteEventRepository, TimeTracker, TrackerError, now

from .config import resolve_db_path
from .formatting import render_report
from .parsing import (
    parse_auto_resume_at,
    parse_date,
    parse_start_time,
    parse_time_spent,
)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="time-tracker",
        description="Controle de tempo gasto por tarefa (SQLite).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument(
        "--start-day",
        nargs="+",
        metavar="TASK_ID [START_TIME]",
        help="Inicia o dia com a tarefa principal. Horario opcional HH:MM (padrao: agora).",
    )
    g.add_argument(
        "--pause",
        nargs="?",
        const=None,
        default=argparse.SUPPRESS,
        metavar="AUTO_RESUME_AT",
        help="Pausa. Horario de retomada opcional HH:MM.",
    )
    p.add_argument(
        "--pause-at",
        metavar="PAUSE_TIME",
        default=None,
        help=(
            "Horario em que a pausa comecou (HH:MM ou 'YYYY-MM-DD HH:MM'). "
            "Use com --pause para registrar uma pausa retroativa. Padrao: agora."
        ),
    )
    g.add_argument("--resume", action="store_true", help="Retoma apos pausa.")
    p.add_argument(
        "--resume-at",
        metavar="RESUME_TIME",
        default=None,
        help=(
            "Horario em que a retomada ocorreu (HH:MM ou 'YYYY-MM-DD HH:MM'). "
            "Use com --resume para registrar uma retomada retroativa. Padrao: agora."
        ),
    )
    g.add_argument(
        "--side-task",
        nargs=3,
        metavar=("TASK_ID", "TIME_SPENT", "DESCRIPTION"),
        help="Lanca tempo numa tarefa paralela.",
    )
    g.add_argument("--change-task", metavar="TASK_ID", help="Troca a tarefa principal.")
    g.add_argument("--end-day", action="store_true", help="Finaliza o dia e imprime a tabela.")
    g.add_argument(
        "--report",
        nargs="?",
        const=None,
        default=argparse.SUPPRESS,
        metavar="DATE",
        help="Tabela parcial de um dia (padrao: hoje). DATE opcional YYYY-MM-DD.",
    )
    g.add_argument("--status", action="store_true", help="Estado atual do dia.")
    g.add_argument("--init", action="store_true", help="Cria/atualiza o schema no banco.")
    return p


def _print_status(tracker: TimeTracker) -> None:
    wd = tracker.today()
    state = tracker.get_day_state(wd)
    if not state.started:
        print(f"Dia {wd}: nao iniciado.")
        return
    situacao = "finalizado" if state.ended else ("pausado" if state.paused else "em andamento")
    print(f"Dia {wd}: {situacao}")
    print(f"  Tarefa principal atual: {state.current_task}")


def main(argv=None, *, default_db: Optional[str] = None) -> int:
    """Ponto de entrada da CLI.

    `default_db` e o caminho do banco usado quando TIMETRACKER_DB nao esta
    definida (ver config.resolve_db_path).
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        repo = SqliteEventRepository(resolve_db_path(default_db))
        repo.init_schema()  # garante schema antes de qualquer operacao de dados
        if args.init:
            print("Schema aplicado com sucesso.")
            return 0

        tracker = TimeTracker(repo)

        if args.start_day:
            if len(args.start_day) > 2:
                raise ValueError(
                    "Use: --start-day TASK_ID [START_TIME]. "
                    "START_TIME aceita HH:MM ou 'YYYY-MM-DD HH:MM'."
                )
            task_id = args.start_day[0]
            start_time = args.start_day[1] if len(args.start_day) == 2 else None
            at = parse_start_time(start_time)
            tracker.start_day(task_id, at=at)
            print(
                f"Dia iniciado com a tarefa principal '{task_id}' "
                f"as {at.strftime('%H:%M')}."
            )

        elif "pause" in vars(args):
            pause_at = parse_start_time(args.pause_at) if args.pause_at else None
            resume_at = parse_auto_resume_at(args.pause, pause_at or now())
            result = tracker.pause(resume_at, at=pause_at)
            quando = f" (retroativo as {pause_at.strftime('%H:%M')})" if pause_at else ""
            if result.explicit:
                print(
                    f"Pausado{quando}. Retomada automatica prevista para "
                    f"{result.auto_resume_at.strftime('%Y-%m-%d %H:%M')}."
                )
            else:
                print(f"Pausado{quando}.")

        elif args.resume:
            resume_at = parse_start_time(args.resume_at) if args.resume_at else None
            tracker.resume(at=resume_at)
            quando = f" (retroativo as {resume_at.strftime('%H:%M')})" if resume_at else ""
            print(f"Retomado{quando}.")

        elif args.change_task:
            tracker.change_task(args.change_task)
            print(f"Tarefa principal trocada para '{args.change_task}'.")

        elif args.side_task:
            task_id, time_spent, description = args.side_task
            minutes = parse_time_spent(time_spent)
            tracker.side_task(task_id, minutes, description)
            print(f"Side-task '{task_id}' lancada: {minutes} min ({description}).")

        elif args.end_day:
            print(render_report(tracker.end_day()))

        elif "report" in vars(args):
            work_date = parse_date(args.report)
            print(render_report(tracker.build_report(work_date)))

        elif args.status:
            _print_status(tracker)

    except (TrackerError, ValueError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
