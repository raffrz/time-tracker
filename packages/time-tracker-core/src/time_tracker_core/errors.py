"""Erros do dominio."""


class TrackerError(Exception):
    """Erro de regra de negocio (estado invalido para a operacao)."""


class NotFoundError(TrackerError):
    """Recurso inexistente (ex.: evento a excluir)."""
