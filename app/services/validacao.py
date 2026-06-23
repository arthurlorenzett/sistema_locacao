"""Validações reutilizáveis (frontend chama os endpoints; aqui é a barreira do backend).

Todas as funções levantam `ValueError` com mensagem amigável em PT-BR quando o
dado é inválido — as rotas capturam e devolvem 400. Isso garante que nenhuma
entrada inconsistente chegue às regras de negócio.
"""

import re
from datetime import datetime

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


def validar_data_horario_futuro(valor) -> datetime:
    """Garante que a data/horário é válida e está no futuro."""
    quando = parse_datetime(valor)
    if quando < datetime.now():
        raise ValueError("A data/horário da reserva deve estar no futuro.")
    return quando


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
