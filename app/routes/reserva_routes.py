"""Rotas de reservas: criação, listagem (cliente/locador), confirmação, cancelamento
e registro de comparecimento (no-show)."""

from flask import Blueprint, request, jsonify, g

from app.facades.reserva_facade import ReservaFacade
from app import db
from app.models.avaliacao_model import Avaliacao
from app.models.reserva_model import Reserva
from app.models.espaco_esportivo_model import EspacoEsportivo
from app.models.usuario_model import Usuario
from app.auth.decorators import login_obrigatorio, requer_perfil
from app.services import avaliacoes, validacao
from app.services.confianca import indice_confianca

reserva_bp = Blueprint('reserva_bp', __name__)


def _reserva_dict(reserva, espaco=None, avaliacao=None):
    """Reserva + dados do espaço + ações possíveis + a avaliação já feita (se houver)."""
    dados = reserva.to_dict()
    if espaco is None:
        espaco = EspacoEsportivo.query.get(reserva.espaco_id)
    if espaco:
        dados["espaco_nome"] = espaco.nome
        dados["espaco_modalidade"] = espaco.tipo_esporte
        dados["espaco_endereco"] = espaco.endereco
        dados["preco_hora"] = espaco.preco_hora
    dados["pode_cancelar"] = (reserva.status_texto in ("Pendente", "Confirmada")
                              and reserva.fim_efetivo > validacao.agora())
    dados["avaliacao"] = avaliacao.resumo() if avaliacao else None
    dados["pode_avaliar"] = avaliacao is None and avaliacoes.motivo_nao_pode_avaliar(reserva) is None
    return dados


def _e_dono_do_espaco(reserva) -> bool:
    """Locador dono do espaço da reserva (ou administrador)."""
    u = g.usuario
    if u.tipo_usuario == 'administrador':
        return True
    espaco = EspacoEsportivo.query.get(reserva.espaco_id)
    return bool(u.tipo_usuario == 'locador' and espaco and espaco.locador_id == u.id)


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
    feitas = avaliacoes.por_reserva([r.id for r in reservas])
    return jsonify({"reservas": [_reserva_dict(r, avaliacao=feitas.get(r.id)) for r in reservas]}), 200


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

    agora = validacao.agora()
    feitas = avaliacoes.por_reserva([r.id for r in reservas])
    clientes = {}  # locatario_id -> (nome, índice de confiança), calculado uma vez por cliente
    itens = []
    for r in reservas:
        if r.locatario_id not in clientes:
            cliente = Usuario.query.get(r.locatario_id)
            clientes[r.locatario_id] = (cliente.nome if cliente else None, indice_confianca(r.locatario_id))
        nome, confianca = clientes[r.locatario_id]
        itens.append(dict(_reserva_dict(r, mapa.get(r.espaco_id), feitas.get(r.id)),
                          locatario_nome=nome, confianca=confianca,
                          pode_registrar_comparecimento=(r.status_texto == "Confirmada"
                                                         and r.fim_efetivo <= agora)))
    return jsonify({"reservas": itens}), 200


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


@reserva_bp.route('/<int:id>/avaliacao', methods=['POST'])
@login_obrigatorio
def avaliar_reserva(id):
    """O locatário avalia o espaço depois de uma reserva realizada ({"nota": 1-5, "comentario"})."""
    reserva = Reserva.query.get(id)
    if not reserva:
        return jsonify({"erro": "Reserva não encontrada."}), 404
    if g.usuario.tipo_usuario != 'locatario' or reserva.locatario_id != g.usuario.id:
        return jsonify({"erro": "Só quem fez a reserva pode avaliá-la."}), 403

    dados = request.get_json(silent=True) or {}
    try:
        nota = avaliacoes.validar_nota(dados.get('nota'))
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    motivo = avaliacoes.motivo_nao_pode_avaliar(reserva)
    if motivo:
        return jsonify({"erro": motivo}), 400
    if Avaliacao.query.filter_by(reserva_id=reserva.id).first():
        return jsonify({"erro": "Você já avaliou esta reserva."}), 409

    comentario = (dados.get('comentario') or '').strip()[:avaliacoes.TAMANHO_MAX_COMENTARIO] or None
    db.session.add(Avaliacao(reserva_id=reserva.id, espaco_id=reserva.espaco_id,
                             locatario_id=reserva.locatario_id, nota=nota, comentario=comentario))
    db.session.commit()
    return jsonify({"mensagem": "Obrigado pela avaliação!"}), 201


@reserva_bp.route('/<int:id>/comparecimento', methods=['PUT'])
@login_obrigatorio
def registrar_comparecimento(id):
    """O locador informa, depois do horário, se o cliente compareceu ({"compareceu": true/false})."""
    reserva = Reserva.query.get(id)
    if not reserva:
        return jsonify({"erro": "Reserva não encontrada."}), 404
    if not _e_dono_do_espaco(reserva):
        return jsonify({"erro": "Só o dono do espaço registra o comparecimento."}), 403

    compareceu = (request.get_json(silent=True) or {}).get('compareceu')
    if not isinstance(compareceu, bool):
        return jsonify({"erro": "Informe compareceu: true ou false."}), 400
    try:
        mensagem = ReservaFacade.registrar_comparecimento(id, compareceu)
        return jsonify({"mensagem": mensagem, "status": reserva.status_texto}), 200
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
