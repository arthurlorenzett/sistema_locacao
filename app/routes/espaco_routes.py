"""Rotas de espaços esportivos (catálogo + CRUD do proprietário).

Listagem/detalhe são públicos (catálogo do cliente); criação/edição/desativação
exigem perfil de locador (dono do espaço) ou administrador.
"""

from datetime import timedelta

from flask import Blueprint, request, jsonify, g

from app import db
from app.models.espaco_esportivo_model import EspacoEsportivo
from app.models.reserva_model import Reserva
from app.auth.decorators import requer_perfil, login_obrigatorio
from app.services import validacao

espaco_bp = Blueprint('espaco_bp', __name__)

# Duração padrão de um slot quando a reserva não tem data_fim definida.
_SLOT_PADRAO = timedelta(hours=1)


def _espaco_ocupado_em(espaco_id, alvo):
    """True se há reserva confirmada sobrepondo o instante `alvo`."""
    confirmadas = Reserva.query.filter_by(espaco_id=espaco_id, status_texto="Confirmada").all()
    for r in confirmadas:
        fim = r.data_fim or (r.data_horario + _SLOT_PADRAO)
        if r.data_horario <= alvo < fim:
            return True
    return False


@espaco_bp.route('', methods=['GET'], strict_slashes=False)
def listar_espacos():
    """Catálogo com filtros: regiao, modalidade, tipo_quadra, preco_min/max, data+hora."""
    try:
        pmin, pmax = validacao.faixa_preco(request.args.get('preco_min'),
                                           request.args.get('preco_max'))
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400

    query = EspacoEsportivo.query.filter_by(ativo=True)

    regiao = (request.args.get('regiao') or '').strip()
    modalidade = (request.args.get('modalidade') or request.args.get('tipo_esporte') or '').strip()
    tipo_quadra = (request.args.get('tipo_quadra') or '').strip()

    if regiao:
        query = query.filter(EspacoEsportivo.regiao.ilike(f"%{regiao}%"))
    if modalidade:
        query = query.filter(EspacoEsportivo.tipo_esporte.ilike(f"%{modalidade}%"))
    if tipo_quadra:
        query = query.filter(EspacoEsportivo.tipo_quadra.ilike(f"%{tipo_quadra}%"))
    if pmin is not None:
        query = query.filter(EspacoEsportivo.preco_hora >= pmin)
    if pmax is not None:
        query = query.filter(EspacoEsportivo.preco_hora <= pmax)

    espacos = query.all()

    # Filtro por disponibilidade em data/horário (opcional).
    data = (request.args.get('data') or '').strip()
    hora = (request.args.get('hora') or '').strip()
    if data and hora:
        try:
            alvo = validacao.parse_datetime(f"{data}T{hora}")
        except ValueError as e:
            return jsonify({"erro": str(e)}), 400
        espacos = [e for e in espacos if not _espaco_ocupado_em(e.id, alvo)]

    return jsonify({
        "espacos": [e.to_dict() for e in espacos],
        "total": len(espacos),
    }), 200


@espaco_bp.route('/meus', methods=['GET'], strict_slashes=False)
@requer_perfil('locador')
def meus_espacos():
    """Lista os espaços do locador autenticado (inclui inativos)."""
    espacos = EspacoEsportivo.query.filter_by(locador_id=g.usuario.id).all()
    return jsonify({"espacos": [e.to_dict() for e in espacos], "total": len(espacos)}), 200


@espaco_bp.route('/<int:id>', methods=['GET'])
def detalhar_espaco(id):
    espaco = EspacoEsportivo.query.get(id)
    if not espaco:
        return jsonify({"erro": "Espaço não encontrado."}), 404
    return jsonify(espaco.to_dict()), 200


@espaco_bp.route('', methods=['POST'], strict_slashes=False)
@requer_perfil('locador')
def criar_espaco():
    dados = request.get_json(silent=True) or {}
    nome = (dados.get('nome') or '').strip()
    modalidade = (dados.get('modalidade') or dados.get('tipo_esporte') or '').strip()
    if not nome or not modalidade:
        return jsonify({"erro": "Nome e modalidade são obrigatórios."}), 400

    try:
        preco = validacao.validar_preco(dados.get('preco_hora'))
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400

    espaco = EspacoEsportivo(
        nome=nome,
        tipo_esporte=modalidade,
        preco_hora=preco,
        locador_id=g.usuario.id,
        regiao=(dados.get('regiao') or None),
        tipo_quadra=(dados.get('tipo_quadra') or None),
        descricao=(dados.get('descricao') or None),
        endereco=(dados.get('endereco') or None),
        foto_url=(dados.get('foto_url') or None),
        aceita_online=bool(dados.get('aceita_online', True)),
        aceita_presencial=bool(dados.get('aceita_presencial', True)),
        disponivel=True,
        ativo=True,
    )
    db.session.add(espaco)
    db.session.commit()
    return jsonify({"mensagem": "Espaço cadastrado com sucesso!", "id": espaco.id}), 201


def _autorizado_a_editar(espaco) -> bool:
    return g.usuario.tipo_usuario == 'administrador' or espaco.locador_id == g.usuario.id


@espaco_bp.route('/<int:id>', methods=['PUT'])
@login_obrigatorio
def editar_espaco(id):
    espaco = EspacoEsportivo.query.get(id)
    if not espaco:
        return jsonify({"erro": "Espaço não encontrado."}), 404
    if not _autorizado_a_editar(espaco):
        return jsonify({"erro": "Você não tem permissão para editar este espaço."}), 403

    dados = request.get_json(silent=True) or {}
    if 'nome' in dados and dados['nome']:
        espaco.nome = dados['nome'].strip()
    if dados.get('modalidade') or dados.get('tipo_esporte'):
        espaco.tipo_esporte = (dados.get('modalidade') or dados.get('tipo_esporte')).strip()
    if 'preco_hora' in dados:
        try:
            espaco.preco_hora = validacao.validar_preco(dados['preco_hora'])
        except ValueError as e:
            return jsonify({"erro": str(e)}), 400
    for campo in ('regiao', 'tipo_quadra', 'descricao', 'endereco', 'foto_url'):
        if campo in dados:
            setattr(espaco, campo, dados[campo] or None)
    for campo in ('aceita_online', 'aceita_presencial', 'disponivel', 'ativo'):
        if campo in dados:
            setattr(espaco, campo, bool(dados[campo]))

    db.session.commit()
    return jsonify({"mensagem": "Espaço atualizado com sucesso!"}), 200


@espaco_bp.route('/<int:id>', methods=['DELETE'])
@login_obrigatorio
def desativar_espaco(id):
    """Remoção lógica: desativa o espaço (preserva histórico de reservas)."""
    espaco = EspacoEsportivo.query.get(id)
    if not espaco:
        return jsonify({"erro": "Espaço não encontrado."}), 404
    if not _autorizado_a_editar(espaco):
        return jsonify({"erro": "Você não tem permissão para remover este espaço."}), 403

    espaco.ativo = False
    espaco.disponivel = False
    db.session.commit()
    return jsonify({"mensagem": "Espaço desativado."}), 200
