"""Índice de confiança do locatário: quanto ele comparece às reservas que faz.

Conta só reservas cujo horário já terminou. Uma reserva confirmada em que o
locador não registrou nada é presumida como comparecimento — o histórico do
cliente não fica pior porque o locador esqueceu de marcar.
"""

from app.models.reserva_model import Reserva
from app.services import validacao


def indice_confianca(locatario_id) -> dict:
    agora = validacao.agora()
    reservas = Reserva.query.filter(
        Reserva.locatario_id == locatario_id,
        Reserva.status_texto.in_(("Confirmada", "Concluída", "Não compareceu")),
        Reserva.data_horario < agora,
    ).all()
    realizadas = [r for r in reservas if r.fim_efetivo <= agora]
    faltas = sum(1 for r in realizadas if r.status_texto == "Não compareceu")
    comparecimentos = len(realizadas) - faltas
    total = comparecimentos + faltas
    return {
        "comparecimentos": comparecimentos,
        "faltas": faltas,
        "percentual": round(100 * comparecimentos / total) if total else None,
    }
