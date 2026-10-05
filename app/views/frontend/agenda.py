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
    return _dia_curto(dia)


def pode_reservar(horarios: list, indice: int, horas: int) -> bool:
    """Há `horas` horários livres e seguidos a partir de `indice`?"""
    trecho = horarios[indice:indice + horas]
    if len(trecho) < horas or not all(h["disponivel"] for h in trecho):
        return False
    return all(a["fim"] == b["inicio"] for a, b in zip(trecho, trecho[1:]))


def periodo_faixa(dia: date, inicio_hhmm: str, fim_hhmm: str) -> tuple:
    """(início, fim) em ISO para a API; um fim "24:00" vira 00:00 do dia seguinte."""
    inicio = f"{dia.isoformat()}T{inicio_hhmm}"
    if fim_hhmm == "24:00":
        return inicio, f"{(dia + timedelta(days=1)).isoformat()}T00:00"
    return inicio, f"{dia.isoformat()}T{fim_hhmm}"


def periodo_reserva(dia: date, horarios: list, indice: int, horas: int) -> tuple:
    """Período de `horas` horários seguidos a partir de `indice` (ver periodo_faixa)."""
    return periodo_faixa(dia, horarios[indice]["inicio"], horarios[indice + horas - 1]["fim"])


def _dia_curto(momento) -> str:
    return f"{_DIAS[momento.weekday()]} {momento:%d/%m}"


def descrever_bloqueio(bloqueio: dict) -> str:
    return descrever_periodo(bloqueio["inicio"], bloqueio["fim"])


def descrever_periodo(inicio_iso: str, fim_iso) -> str:
    """Texto curto de um período: "Ter 06/10 · dia inteiro", "Ter 06/10 · 09:00–11:00"...

    Sem fim informado (reservas antigas), vale a duração padrão de 1 hora.
    """
    inicio = datetime.fromisoformat(inicio_iso)
    fim = datetime.fromisoformat(fim_iso) if fim_iso else inicio + timedelta(hours=1)
    meia_noite = datetime.combine(inicio.date(), datetime.min.time())

    if inicio == meia_noite and fim.time() == datetime.min.time():
        ultimo_dia = fim - timedelta(days=1)
        if ultimo_dia.date() == inicio.date():
            return f"{_dia_curto(inicio)} · dia inteiro"
        return f"{_dia_curto(inicio)} a {_dia_curto(ultimo_dia)} · dias inteiros"
    if fim == meia_noite + timedelta(days=1):
        return f"{_dia_curto(inicio)} · {inicio:%H:%M}–24:00"
    if fim.date() == inicio.date():
        return f"{_dia_curto(inicio)} · {inicio:%H:%M}–{fim:%H:%M}"
    return f"{_dia_curto(inicio)} {inicio:%H:%M} → {_dia_curto(fim)} {fim:%H:%M}"


def valor_reserva(horarios: list, indice: int, horas: int) -> float:
    """Valor de `horas` horários seguidos a partir de `indice` (cada horário traz o seu preço)."""
    return round(sum(h["preco"] for h in horarios[indice:indice + horas]), 2)
