"""Validações reutilizáveis (frontend chama os endpoints; aqui é a barreira do backend).

Todas as funções levantam `ValueError` com mensagem amigável em PT-BR quando o
dado é inválido — as rotas capturam e devolvem 400. Isso garante que nenhuma
entrada inconsistente chegue às regras de negócio.
"""

import re
from datetime import datetime
from zoneinfo import ZoneInfo

# Datas trafegam "ingênuas" (sem fuso) no horário de Brasília. O servidor (Render)
# roda em UTC, então "agora" precisa ser calculado explicitamente neste fuso.
FUSO = ZoneInfo("America/Sao_Paulo")

_RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Formatos de data/hora aceitos vindos do frontend (Flet/ISO).
_FORMATOS_DATA = (
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
)


def validar_email(email: str) -> str:
    email = (email or "").strip()
    if not _RE_EMAIL.match(email):
        raise ValueError("E-mail em formato inválido.")
    return email


def _so_digitos(valor: str) -> str:
    return re.sub(r"\D", "", valor or "")


def validar_cpf(cpf: str) -> str:
    digitos = _so_digitos(cpf)
    if len(digitos) != 11:
        raise ValueError("CPF deve conter 11 dígitos.")
    return cpf.strip()


def validar_cnpj(cnpj: str) -> str:
    digitos = _so_digitos(cnpj)
    if len(digitos) != 14:
        raise ValueError("CNPJ deve conter 14 dígitos.")
    return cnpj.strip()


def validar_preco(valor) -> float:
    try:
        preco = float(valor)
    except (TypeError, ValueError):
        raise ValueError("Preço inválido.")
    if preco <= 0:
        raise ValueError("O preço por hora deve ser maior que zero.")
    return preco


def parse_datetime(valor) -> datetime:
    """Converte string em datetime; aceita ISO e formatos do frontend."""
    if isinstance(valor, datetime):
        return valor
    if not valor or not isinstance(valor, str):
        raise ValueError("Data/horário não informado.")
    texto = valor.strip().replace("Z", "")
    for fmt in _FORMATOS_DATA:
        try:
            return datetime.strptime(texto, fmt)
        except ValueError:
            continue
    raise ValueError("Data/horário em formato inválido.")


def agora() -> datetime:
    """Data/hora atual no horário de Brasília, sem fuso (mesmo formato das reservas)."""
    return datetime.now(FUSO).replace(tzinfo=None)


def validar_data_horario_futuro(valor) -> datetime:
    """Garante que a data/horário é válida e está no futuro."""
    quando = parse_datetime(valor)
    if quando < agora():
        raise ValueError("A data/horário da reserva deve estar no futuro.")
    return quando


def parse_hora(texto) -> int:
    """Converte "HH:MM" (00:00 a 24:00) em minutos desde a meia-noite."""
    try:
        horas, minutos = (int(p) for p in str(texto).strip().split(":"))
    except (TypeError, ValueError):
        raise ValueError(f"Horário inválido: {texto!r} (use HH:MM).")
    total = horas * 60 + minutos
    if not (0 <= horas <= 24 and 0 <= minutos < 60 and total <= 24 * 60):
        raise ValueError(f"Horário inválido: {texto!r} (use HH:MM).")
    return total


def formatar_hora(minutos: int) -> str:
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


def validar_horarios(horarios) -> list:
    """Valida a grade semanal de funcionamento.

    Recebe `[{"dia_semana": 0-6, "abre": "HH:MM", "fecha": "HH:MM"}, ...]`
    (0 = segunda) e devolve `[(dia, abertura_min, fechamento_min), ...]`.
    """
    if not isinstance(horarios, list) or not horarios:
        raise ValueError("Informe ao menos um dia de funcionamento.")
    resultado, dias = [], set()
    for h in horarios:
        try:
            dia = int(h.get("dia_semana"))
        except (AttributeError, TypeError, ValueError):
            raise ValueError("Dia da semana inválido.")
        if not 0 <= dia <= 6:
            raise ValueError("Dia da semana inválido.")
        if dia in dias:
            raise ValueError("Cada dia da semana só pode ter um horário.")
        abre, fecha = parse_hora(h.get("abre")), parse_hora(h.get("fecha"))
        if fecha <= abre:
            raise ValueError("O horário de fechamento deve ser depois da abertura.")
        dias.add(dia)
        resultado.append((dia, abre, fecha))
    return sorted(resultado)


def validar_regras_preco(regras) -> list:
    """Valida as regras de preço por horário (a lista pode ser vazia).

    Recebe `[{"dias": [0-6, ...], "inicio": "HH:MM", "fim": "HH:MM", "preco_hora": n}, ...]`
    e devolve uma linha por dia: `[(dia, inicio_min, fim_min, preco), ...]`.
    """
    if not isinstance(regras, list):
        raise ValueError("Regras de preço inválidas.")
    linhas = []
    for regra in regras:
        if not isinstance(regra, dict):
            raise ValueError("Regras de preço inválidas.")
        dias = regra.get("dias")
        if not isinstance(dias, list) or not dias:
            raise ValueError("Cada regra de preço precisa de ao menos um dia da semana.")
        if any(isinstance(d, bool) or not isinstance(d, int) or not 0 <= d <= 6 for d in dias):
            raise ValueError("Dia da semana inválido.")
        inicio, fim = parse_hora(regra.get("inicio")), parse_hora(regra.get("fim"))
        if fim <= inicio:
            raise ValueError("Na regra de preço, o fim deve ser depois do início.")
        preco = validar_preco(regra.get("preco_hora"))
        linhas.extend((dia, inicio, fim, preco) for dia in set(dias))

    linhas.sort()
    for (dia_a, _, fim_a, _), (dia_b, inicio_b, _, _) in zip(linhas, linhas[1:]):
        if dia_a == dia_b and inicio_b < fim_a:
            raise ValueError("Há regras de preço sobrepostas no mesmo dia: cada horário só pode ter um preço.")
    return linhas


MAX_SEMANAS_SERIE = 12


def validar_semanas(valor) -> int:
    """Quantidade de semanas de uma reserva recorrente (de 2 a 12)."""
    if isinstance(valor, bool) or not isinstance(valor, int) or not 2 <= valor <= MAX_SEMANAS_SERIE:
        raise ValueError(f"A reserva recorrente deve ter de 2 a {MAX_SEMANAS_SERIE} semanas.")
    return valor


def faixa_preco(preco_min, preco_max):
    """Normaliza filtros de faixa de preço (qualquer um pode ser None)."""
    def _num(v):
        if v in (None, ""):
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            raise ValueError("Faixa de preço inválida.")
    pmin, pmax = _num(preco_min), _num(preco_max)
    if pmin is not None and pmax is not None and pmin > pmax:
        raise ValueError("Faixa de preço inconsistente (mínimo maior que máximo).")
    return pmin, pmax
