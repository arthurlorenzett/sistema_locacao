"""Avaliações dos espaços: quem pode avaliar, média por espaço e avaliações por reserva.

Só avalia quem jogou: a reserva precisa estar concluída ou confirmada com o
horário já encerrado. Falta registrada (no-show) impede — e remove — a avaliação.
"""

from sqlalchemy import func

from app import db
from app.models.avaliacao_model import Avaliacao
from app.services import validacao

TAMANHO_MAX_COMENTARIO = 1000


def motivo_nao_pode_avaliar(reserva):
    """None se a reserva pode ser avaliada; senão, a explicação para o cliente."""
    if reserva.status_texto == "Não compareceu":
        return "Só quem compareceu à reserva pode avaliar."
    if reserva.status_texto not in ("Confirmada", "Concluída"):
        return "Só reservas realizadas podem ser avaliadas."
    if reserva.status_texto == "Confirmada" and reserva.fim_efetivo > validacao.agora():
        return "Você poderá avaliar depois do horário da reserva."
    return None


def validar_nota(valor) -> int:
    # bool é subclasse de int em Python; True não é uma nota.
    if isinstance(valor, bool) or not isinstance(valor, int) or not 1 <= valor <= 5:
        raise ValueError("A nota deve ser um número inteiro de 1 a 5.")
    return valor


def resumo_do_espaco(espaco_id) -> dict:
    """{"nota_media": 4.5 | None, "total_avaliacoes": n} do espaço."""
    media, total = db.session.query(func.avg(Avaliacao.nota), func.count(Avaliacao.id)) \
        .filter(Avaliacao.espaco_id == espaco_id).one()
    return {"nota_media": round(float(media), 1) if total else None, "total_avaliacoes": total}


def por_reserva(reserva_ids) -> dict:
    """reserva_id -> Avaliacao, numa consulta só (para montar listas de reservas)."""
    if not reserva_ids:
        return {}
    avaliacoes = Avaliacao.query.filter(Avaliacao.reserva_id.in_(reserva_ids)).all()
    return {a.reserva_id: a for a in avaliacoes}


def remover_da_reserva(reserva_id) -> None:
    """Usado quando o locador registra falta: quem não compareceu não avalia."""
    Avaliacao.query.filter_by(reserva_id=reserva_id).delete()
