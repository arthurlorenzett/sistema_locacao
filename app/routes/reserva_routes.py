"""Rotas de reservas: criação, listagem (cliente/locador), confirmação e cancelamento."""

from flask import Blueprint, request, jsonify, g

from app.facades.reserva_facade import ReservaFacade
from app.models.reserva_model import Reserva
from app.models.espaco_esportivo_model import EspacoEsportivo
from app.auth.decorators import login_obrigatorio, requer_perfil

reserva_bp = Blueprint('reserva_bp', __name__)


def _reserva_dict(reserva, espaco=None):
    dados = reserva.to_dict()
    if espaco is None:
        espaco = EspacoEsportivo.query.get(reserva.espaco_id)
    if espaco:
        dados["espaco_nome"] = espaco.nome
        dados["espaco_modalidade"] = espaco.tipo_esporte
        dados["espaco_endereco"] = espaco.endereco
        dados["preco_hora"] = espaco.preco_hora
    return dados


def _pode_gerenciar(reserva) -> bool:
    """Cliente dono da reserva, locador dono do espaço ou administrador."""
    u = g.usuario
    if u.tipo_usuario == 'administrador':
        return True
    if u.tipo_usuario == 'locatario' and reserva.locatario_id == u.id:
        return True
    if u.tipo_usuario == 'locador':
        espaco = EspacoEsportivo.query.get(reserva.espaco_id)
        return bool(espaco and espaco.locador_id == u.id)
    return False


@reserva_bp.route('/realizar', methods=['POST'], strict_slashes=False)
@requer_perfil('locatario')
def realizar_reserva():
    """O locatário autenticado solicita um agendamento (nasce Pendente)."""
    dados = request.get_json(silent=True) or {}
    try:
        nova = ReservaFacade.realizar_reserva(
            locatario_id=g.usuario.id,
            espaco_id=dados.get('espaco_id'),
            data_horario=dados.get('data_horario'),
            data_fim=dados.get('data_fim'),
        )
        return jsonify({
            "mensagem": "Pedido de reserva realizado com sucesso!",
            "reserva_id": nova.id,
            "status": nova.status_texto,
        }), 201
    except ValueError as e:
        print("ERRO RESERVA:", str(e))
        return jsonify({"erro": str(e)}), 400


@reserva_bp.route('', methods=['GET'], strict_slashes=False)
@requer_perfil('locatario')
def minhas_reservas():
    """Lista as reservas do locatário autenticado (histórico + ativas)."""
    reservas = (Reserva.query
                .filter_by(locatario_id=g.usuario.id)
                .order_by(Reserva.data_horario.desc())
                .all())
    return jsonify({"reservas": [_reserva_dict(r) for r in reservas]}), 200


@reserva_bp.route('/recebidas', methods=['GET'], strict_slashes=False)
@requer_perfil('locador')
def reservas_recebidas():
    """Lista as reservas dos espaços do locador autenticado."""
    espacos = EspacoEsportivo.query.filter_by(locador_id=g.usuario.id).all()
    ids = [e.id for e in espacos]
    mapa = {e.id: e for e in espacos}
    if not ids:
        return jsonify({"reservas": []}), 200
    reservas = (Reserva.query
                .filter(Reserva.espaco_id.in_(ids))
                .order_by(Reserva.data_horario.desc())
                .all())
    return jsonify({"reservas": [_reserva_dict(r, mapa.get(r.espaco_id)) for r in reservas]}), 200


@reserva_bp.route('/<int:id>/confirmar', methods=['PUT'])
@login_obrigatorio
def confirmar_reserva(id):
    """Confirma a reserva registrando o pagamento (online/presencial, simulado)."""
    reserva = Reserva.query.get(id)
    if not reserva:
        return jsonify({"erro": "Reserva não encontrada."}), 404
    if not _pode_gerenciar(reserva):
        return jsonify({"erro": "Sem permissão sobre esta reserva."}), 403

    dados = request.get_json(silent=True) or {}
    try:
        mensagem = ReservaFacade.confirmar_pagamento_e_reserva(id, dados.get('metodo_pagamento'))
        return jsonify({"mensagem": mensagem, "status": reserva.status_texto,
                        "status_pagamento": reserva.status_pagamento}), 200
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400


@reserva_bp.route('/<int:id>/cancelar', methods=['PUT'])
@login_obrigatorio
def cancelar_reserva(id):
    reserva = Reserva.query.get(id)
    if not reserva:
        return jsonify({"erro": "Reserva não encontrada."}), 404
    if not _pode_gerenciar(reserva):
        return jsonify({"erro": "Sem permissão sobre esta reserva."}), 403

    try:
        mensagem = ReservaFacade.cancelar_reserva(id)
        return jsonify({"mensagem": mensagem, "status": reserva.status_texto}), 200
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
