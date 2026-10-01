"""Bloqueio manual de agenda: o dono fecha horários/dias do espaço para reservas online."""

from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify, g

from app import db
from app.models.bloqueio_model import Bloqueio
from app.models.espaco_esportivo_model import EspacoEsportivo
from app.auth.decorators import login_obrigatorio
from app.services import agenda, validacao

bloqueio_bp = Blueprint('bloqueio_bp', __name__)


def _espaco_do_dono(espaco_id):
    """(espaco, None) se o usuário logado pode gerenciar a agenda; senão (None, resposta de erro)."""
    espaco = EspacoEsportivo.query.get(espaco_id)
    if not espaco:
        return None, (jsonify({"erro": "Espaço não encontrado."}), 404)
    if g.usuario.tipo_usuario != 'administrador' and espaco.locador_id != g.usuario.id:
        return None, (jsonify({"erro": "Você não tem permissão para gerenciar a agenda deste espaço."}), 403)
    return espaco, None


def _periodo(dados):
    """(inicio, fim) a partir de {data, dia_inteiro} ou {inicio, fim}; levanta ValueError."""
    if dados.get('dia_inteiro'):
        try:
            dia = datetime.strptime(str(dados.get('data') or ''), "%Y-%m-%d")
        except ValueError:
            raise ValueError("Data inválida (use AAAA-MM-DD).")
        return dia, dia + timedelta(days=1)

    if not dados.get('inicio') or not dados.get('fim'):
        raise ValueError("Informe o início e o fim do bloqueio.")
    inicio, fim = validacao.parse_datetime(dados['inicio']), validacao.parse_datetime(dados['fim'])
    if fim <= inicio:
        raise ValueError("O fim do bloqueio deve ser depois do início.")
    return inicio, fim


@bloqueio_bp.route('/<int:espaco_id>/bloqueios', methods=['GET'])
@login_obrigatorio
def listar_bloqueios(espaco_id):
    """Bloqueios que ainda não terminaram, em ordem cronológica."""
    espaco, erro = _espaco_do_dono(espaco_id)
    if erro:
        return erro
    bloqueios = (Bloqueio.query
                 .filter(Bloqueio.espaco_id == espaco.id, Bloqueio.fim > validacao.agora())
                 .order_by(Bloqueio.inicio).all())
    return jsonify({"bloqueios": [b.to_dict() for b in bloqueios]}), 200


@bloqueio_bp.route('/<int:espaco_id>/bloqueios', methods=['POST'])
@login_obrigatorio
def criar_bloqueio(espaco_id):
    espaco, erro = _espaco_do_dono(espaco_id)
    if erro:
        return erro

    dados = request.get_json(silent=True) or {}
    try:
        inicio, fim = _periodo(dados)
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    if fim <= validacao.agora():
        return jsonify({"erro": "Esse período já passou."}), 400

    # Não tira a quadra de quem já reservou: o locador cancela a reserva antes.
    em_conflito = agenda.periodos_reservados(espaco.id, inicio, fim, status=("Pendente", "Confirmada"))
    if em_conflito:
        return jsonify({"erro": f"Há {len(em_conflito)} reserva(s) neste período. "
                                "Cancele-as em \"Reservas\" antes de bloquear."}), 409

    motivo = (dados.get('motivo') or '').strip()[:200] or None
    bloqueio = Bloqueio(espaco_id=espaco.id, inicio=inicio, fim=fim, motivo=motivo)
    db.session.add(bloqueio)
    db.session.commit()
    return jsonify({"mensagem": "Horário bloqueado.", "id": bloqueio.id}), 201


@bloqueio_bp.route('/<int:espaco_id>/bloqueios/<int:bloqueio_id>', methods=['DELETE'])
@login_obrigatorio
def remover_bloqueio(espaco_id, bloqueio_id):
    espaco, erro = _espaco_do_dono(espaco_id)
    if erro:
        return erro
    bloqueio = Bloqueio.query.filter_by(id=bloqueio_id, espaco_id=espaco.id).first()
    if not bloqueio:
        return jsonify({"erro": "Bloqueio não encontrado."}), 404
    db.session.delete(bloqueio)
    db.session.commit()
    return jsonify({"mensagem": "Bloqueio removido."}), 200
