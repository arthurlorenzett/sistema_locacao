"""Regras da escolha de dia/horário no diálogo de reserva (sem dependência do Flet)."""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

FUSO = ZoneInfo("America/Sao_Paulo")
_DIAS = ("Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom")


def hoje() -> date:
    """Data de hoje em Brasília (o servidor do frontend roda em UTC)."""
    return datetime.now(FUSO).date()


def proximos_dias(inicio: date, quantidade: int = 14) -> list:
    return [inicio + timedelta(days=i) for i in range(quantidade)]


def rotulo_dia(dia: date, referencia: date) -> str:
    if dia == referencia:
        return "Hoje"
    if dia == referencia + timedelta(days=1):
        return "Amanhã"
    return f"{_DIAS[dia.weekday()]} {dia:%d/%m}"


def pode_reservar(horarios: list, indice: int, horas: int) -> bool:
    """Há `horas` horários livres e seguidos a partir de `indice`?"""
    trecho = horarios[indice:indice + horas]
    if len(trecho) < horas or not all(h["disponivel"] for h in trecho):
        return False
    return all(a["fim"] == b["inicio"] for a, b in zip(trecho, trecho[1:]))


def periodo_reserva(dia: date, horarios: list, indice: int, horas: int) -> tuple:
    """(início, fim) em ISO para a API; um fim "24:00" vira 00:00 do dia seguinte."""
    inicio = f"{dia.isoformat()}T{horarios[indice]['inicio']}"
    fim_hhmm = horarios[indice + horas - 1]["fim"]
    if fim_hhmm == "24:00":
        return inicio, f"{(dia + timedelta(days=1)).isoformat()}T00:00"
    return inicio, f"{dia.isoformat()}T{fim_hhmm}"
