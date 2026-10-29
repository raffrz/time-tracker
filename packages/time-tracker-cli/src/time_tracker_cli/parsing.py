"""Interpretacao de entradas de texto digitadas na linha de comando."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional

from time_tracker_core import now, today

_DATETIME_FORMATS = ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M")


def _parse_absolute(value: str, reference: datetime) -> Optional[datetime]:
    for fmt in _DATETIME_FORMATS:
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=reference.tzinfo)
        except ValueError:
            pass
    return None


def _parse_clock(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%H:%M")
    except ValueError as exc:
        raise ValueError(
            f"Formato de horario invalido: '{value}'. Use HH:MM ou 'YYYY-MM-DD HH:MM'."
        ) from exc


def parse_start_time(value: Optional[str], reference: Optional[datetime] = None) -> datetime:
    """Interpreta um horario (--start-day, --pause-at, --resume-at).

    - None               -> reference (agora).
    - 'HH:MM'            -> data de reference nesse horario.
    - 'YYYY-MM-DD HH:MM' -> data/hora absoluta.
    """
    reference = reference or now()
    if value is None:
        return reference

    value = value.strip()
    absolute = _parse_absolute(value, reference)
    if absolute is not None:
        return absolute

    t = _parse_clock(value)
    return reference.replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)


def parse_date(value: Optional[str], reference: Optional[date] = None) -> date:
    """Interpreta uma data para o relatorio ('YYYY-MM-DD'; None -> hoje)."""
    reference = reference or today()
    if value is None:
        return reference

    value = value.strip()
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(
            f"Formato de data invalido: '{value}'. Use YYYY-MM-DD."
        ) from exc


def parse_auto_resume_at(value: Optional[str], reference: datetime) -> Optional[datetime]:
    """Interpreta o argumento de --pause.

    - None               -> None (sem retomada informada; o core assume o padrao).
    - 'HH:MM'            -> na data de reference nesse horario; se ja passou, amanha.
    - 'YYYY-MM-DD HH:MM' -> data/hora absoluta.
    """
    if value is None:
        return None

    value = value.strip()
    absolute = _parse_absolute(value, reference)
    if absolute is not None:
        return absolute

    t = _parse_clock(value)
    candidate = reference.replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)
    if candidate <= reference:
        candidate += timedelta(days=1)
    return candidate


def parse_time_spent(value: str) -> int:
    """Converte '90', '1h30', '1h30m', '1:30', '45m' em minutos."""
    value = value.strip().lower()
    if value.isdigit():
        return int(value)
    if ":" in value:
        h, m = value.split(":", 1)
        return int(h) * 60 + int(m)
    minutes = 0
    if "h" in value:
        h_part, rest = value.split("h", 1)
        minutes += int(h_part) * 60 if h_part else 0
        value = rest
    value = value.replace("m", "").strip()
    if value:
        minutes += int(value)
    return minutes
