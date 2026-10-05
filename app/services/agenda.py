"""Agenda dos espaços: o que está ocupado/bloqueado e quais horários de um dia estão livres.

É o único lugar que decide se um período está livre — usado pela reserva
(fachada), pela busca do catálogo e pela grade de horários exibida ao cliente.
"""

from datetime import datetime, time, timedelta

from app.models.bloqueio_model import Bloqueio
from app.models.reserva_model import Reserva
from app.services import precos, validacao

# Duração de cada horário oferecido (e de uma reserva sem término informado).
DURACAO_SLOT = timedelta(hours=1)

# Espaços antigos, sem grade cadastrada, aceitam qualquer horário; para montar a
# grade exibida ao cliente usa-se esta janela (a mesma sugerida no cadastro).
_JANELA_PADRAO = (8 * 60, 22 * 60)


def periodos_reservados(espaco_id, inicio, fim, ignorar_reserva_id=None, status=("Confirmada",)):
    """Períodos (inicio, fim) de reservas (por padrão, só confirmadas) que se sobrepõem a [inicio, fim)."""
    reservas = Reserva.query.filter(
        Reserva.espaco_id == espaco_id,
        Reserva.status_texto.in_(status),
        Reserva.data_horario < fim,
    ).all()
    periodos = []
    for r in reservas:
        if r.id == ignorar_reserva_id:
            continue
        if r.fim_efetivo > inicio:
            periodos.append((r.data_horario, r.fim_efetivo))
    return periodos


def esta_reservado(espaco_id, inicio, fim, ignorar_reserva_id=None) -> bool:
    return bool(periodos_reservados(espaco_id, inicio, fim, ignorar_reserva_id))


def bloqueios_no_periodo(espaco_id, inicio, fim):
    """Bloqueios do locador que se sobrepõem a [inicio, fim)."""
    return Bloqueio.query.filter(
        Bloqueio.espaco_id == espaco_id, Bloqueio.inicio < fim, Bloqueio.fim > inicio,
    ).order_by(Bloqueio.inicio).all()


def esta_bloqueado(espaco_id, inicio, fim) -> bool:
    return bool(bloqueios_no_periodo(espaco_id, inicio, fim))


def livre(espaco, inicio, fim) -> bool:
    """O espaço atende nesse período, que não está bloqueado nem reservado."""
    return (espaco.atende(inicio, fim)
            and not esta_bloqueado(espaco.id, inicio, fim)
            and not esta_reservado(espaco.id, inicio, fim))


def _janela(espaco, data):
    """(abertura, fechamento) em minutos no dia, ou None se o espaço não abre."""
    if not espaco.horarios:
        return _JANELA_PADRAO
    h = espaco.horario_do_dia(data.weekday())
    return (h.abertura, h.fechamento) if h else None


def _hhmm(momento, meia_noite):
    return "24:00" if momento == meia_noite + timedelta(days=1) else momento.strftime("%H:%M")


def grade_do_dia(espaco, data):
    """Horários de uma hora dentro do funcionamento do dia, com o motivo de estar indisponível.

    motivo: None (livre) | "passado" (já começou) | "bloqueado" (pelo locador) | "reservado".
    """
    janela = _janela(espaco, data)
    if not janela:
        return []
    meia_noite = datetime.combine(data, time())
    abre = meia_noite + timedelta(minutes=janela[0])
    fecha = meia_noite + timedelta(minutes=janela[1])
    reservados = periodos_reservados(espaco.id, abre, fecha)
    bloqueados = [(b.inicio, b.fim) for b in bloqueios_no_periodo(espaco.id, abre, fecha)]
    agora = validacao.agora()

    horarios, inicio = [], abre
    while inicio + DURACAO_SLOT <= fecha:
        fim = inicio + DURACAO_SLOT
        if inicio < agora:
            motivo = "passado"
        elif any(b_ini < fim and inicio < b_fim for b_ini, b_fim in bloqueados):
            motivo = "bloqueado"
        elif any(r_ini < fim and inicio < r_fim for r_ini, r_fim in reservados):
            motivo = "reservado"
        else:
            motivo = None
        horarios.append({"inicio": _hhmm(inicio, meia_noite), "fim": _hhmm(fim, meia_noite),
                         "disponivel": motivo is None, "motivo": motivo,
                         "preco": precos.preco_do_periodo(espaco, inicio, fim)})
        inicio = fim
    return horarios


def livre_hoje(espaco) -> bool:
    """Ainda há algum horário livre hoje (horário de Brasília)."""
    return any(h["disponivel"] for h in grade_do_dia(espaco, validacao.agora().date()))
