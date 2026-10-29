"""Apresentacao textual de relatorios (horas decimais com virgula)."""
from __future__ import annotations

from datetime import timedelta

from time_tracker_core import DayReport


def format_hours_decimal(total: timedelta) -> str:
    """Converte uma duracao em horas decimais com virgula (7h30m -> '7,50')."""
    hours = total.total_seconds() / 3600.0
    return f"{hours:.2f}".replace(".", ",")


def render_report(report: DayReport) -> str:
    """Monta a tabela de saida com horas decimais (virgula)."""
    lines = []
    lines.append(f"Relatorio do dia {report.work_date}")
    if report.started_at:
        lines.append(f"  Inicio: {report.started_at.strftime('%H:%M')}")
    if report.ended_at:
        lines.append(f"  Fim:    {report.ended_at.strftime('%H:%M')}")
    elif report.open_day:
        lines.append("  (dia em andamento - parcial ate agora)")
    lines.append("")

    rows = []  # (tipo, task, horas_decimal, timedelta)
    for task_id, dur in sorted(report.main_durations.items()):
        rows.append(("principal", task_id, format_hours_decimal(dur), dur))
    for task_id, dur in sorted(report.side_durations.items()):
        rows.append(("side-task", task_id, format_hours_decimal(dur), dur))

    # larguras
    w_type = max([len("Tipo")] + [len(r[0]) for r in rows]) if rows else len("Tipo")
    w_task = max([len("Tarefa")] + [len(str(r[1])) for r in rows]) if rows else len("Tarefa")
    w_hrs = max([len("Horas")] + [len(r[2]) for r in rows]) if rows else len("Horas")

    header = f"  {'Tipo'.ljust(w_type)}  {'Tarefa'.ljust(w_task)}  {'Horas'.rjust(w_hrs)}"
    sep = "  " + "-" * (w_type + w_task + w_hrs + 4)
    lines.append(header)
    lines.append(sep)
    for tipo, task, hrs, _dur in rows:
        lines.append(f"  {tipo.ljust(w_type)}  {str(task).ljust(w_task)}  {hrs.rjust(w_hrs)}")
    lines.append(sep)

    total_all = sum(report.main_durations.values(), timedelta()) + sum(
        report.side_durations.values(), timedelta()
    )
    lines.append(
        f"  {'TOTAL'.ljust(w_type)}  {''.ljust(w_task)}  "
        f"{format_hours_decimal(total_all).rjust(w_hrs)}"
    )
    lines.append(
        f"  {'Pausas'.ljust(w_type)}  {''.ljust(w_task)}  "
        f"{format_hours_decimal(report.total_paused).rjust(w_hrs)}"
    )
    return "\n".join(lines)
