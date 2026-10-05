"""Rotas de espaços esportivos (catálogo + CRUD do proprietário).

Listagem/detalhe são públicos (catálogo do cliente); criação/edição/desativação
exigem perfil de locador (dono do espaço) ou administrador.
"""

from datetime import datetime

from flask import Blueprint, request, jsonify, g

from app import db
from app.models.espaco_esportivo_model import EspacoEsportivo
from app.auth.decorators import requer_perfil, login_obrigatorio, usuario_do_token
from app.models.avaliacao_model import Avaliacao
from app.models.usuario_model import Usuario
from app.services import agenda, avaliacoes, validacao
from app.services.catalogo import dict_catalogo, ids_favoritos

espaco_bp = Blueprint('espaco_bp', __name__)


@espaco_bp.route('', methods=['GET'], strict_slashes=False)
def listar_espacos():
    """Catálogo com filtros: regiao, modalidade, tipo_quadra, preco_min/max, data+hora,
    disponivel_hoje (só espaços com algum horário livre hoje), nota_min (avaliação mínima)."""
    try:
        pmin, pmax = validacao.faixa_preco(request.args.get('preco_min'),
                                           request.args.get('preco_max'))
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    try:
        nota_min = float(request.args['nota_min']) if request.args.get('nota_min') else None
    except ValueError:
        return jsonify({"erro": "Avaliação mínima inválida."}), 400

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
        espacos = [e for e in espacos if agenda.livre(e, alvo, alvo + agenda.DURACAO_SLOT)]

    # Catálogo é público; se quem pede é um locatário logado, marca os favoritos dele.
    usuario, _erro, _status = usuario_do_token()
    favoritos = ids_favoritos(usuario.id) if usuario and usuario.tipo_usuario == 'locatario' else set()

    itens = [dict_catalogo(e, favoritos) for e in espacos]
    if request.args.get('disponivel_hoje') in ('1', 'true'):
        itens = [i for i in itens if i["livre_hoje"]]
    if nota_min is not None:
        # Espaço ainda sem avaliações não entra quando se pede uma nota mínima.
        itens = [i for i in itens if i["nota_media"] is not None and i["nota_media"] >= nota_min]

    return jsonify({"espacos": itens, "total": len(itens)}), 200


@espaco_bp.route('/meus', methods=['GET'], strict_slashes=False)
@requer_perfil('locador')
def meus_espacos():
    """Lista os espaços do locador autenticado (inclui inativos)."""
    espacos = EspacoEsportivo.query.filter_by(locador_id=g.usuario.id).all()
    return jsonify({"espacos": [dict_catalogo(e) for e in espacos], "total": len(espacos)}), 200


@espaco_bp.route('/<int:id>', methods=['GET'])
def detalhar_espaco(id):
    espaco = EspacoEsportivo.query.get(id)
    if not espaco:
        return jsonify({"erro": "Espaço não encontrado."}), 404
    return jsonify(dict(espaco.to_dict(), **avaliacoes.resumo_do_espaco(espaco.id))), 200


@espaco_bp.route('/<int:id>/avaliacoes', methods=['GET'])
def listar_avaliacoes(id):
    """Avaliações do espaço (mais recentes primeiro), com média e total. Pública."""
    if not EspacoEsportivo.query.get(id):
        return jsonify({"erro": "Espaço não encontrado."}), 404
    linhas = (db.session.query(Avaliacao, Usuario.nome)
              .join(Usuario, Usuario.id == Avaliacao.locatario_id)
              .filter(Avaliacao.espaco_id == id)
              .order_by(Avaliacao.created_at.desc(), Avaliacao.id.desc())
              .limit(50).all())
    resumo = avaliacoes.resumo_do_espaco(id)
    return jsonify({
        "media": resumo["nota_media"],
        "total": resumo["total_avaliacoes"],
        "avaliacoes": [{
            "nota": a.nota,
            "comentario": a.comentario,
            "autor": (nome or "Cliente").split()[0],  # só o primeiro nome
            "data": a.created_at.date().isoformat() if a.created_at else None,
        } for a, nome in linhas],
    }), 200


@espaco_bp.route('/<int:id>/disponibilidade', methods=['GET'])
def disponibilidade(id):
    """Horários do dia (?data=AAAA-MM-DD, padrão hoje) com o que está livre para reservar."""
    espaco = EspacoEsportivo.query.get(id)
    if not espaco or not espaco.ativo:
        return jsonify({"erro": "Espaço não encontrado."}), 404

    texto = (request.args.get('data') or '').strip()
    try:
        data = datetime.strptime(texto, "%Y-%m-%d").date() if texto else validacao.agora().date()
    except ValueError:
        return jsonify({"erro": "Data inválida (use AAAA-MM-DD)."}), 400

    horario = espaco.horario_do_dia(data.weekday())
    if not espaco.horarios:
        funcionamento = "Horário não informado"
    elif horario:
        d = horario.to_dict()
        funcionamento = f"{d['abre']}–{d['fecha']}"
    else:
        funcionamento = None

    return jsonify({
        "data": data.isoformat(),
        "dia_semana": data.weekday(),
        "funcionamento": funcionamento,
        "horarios": agenda.grade_do_dia(espaco, data),
    }), 200


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
        grade = validacao.validar_horarios(dados['horarios']) if 'horarios' in dados else None
        regras = validacao.validar_regras_preco(dados.get('regras_preco') or [])
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
    if grade:
        espaco.definir_horarios(grade)
    espaco.definir_regras_preco(regras)
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
    if 'regras_preco' in dados:
        try:
            espaco.definir_regras_preco(validacao.validar_regras_preco(dados['regras_preco'] or []))
        except ValueError as e:
            db.session.rollback()
            return jsonify({"erro": str(e)}), 400
    if 'horarios' in dados:
        try:
            espaco.definir_horarios(validacao.validar_horarios(dados['horarios']))
        except ValueError as e:
            db.session.rollback()
            return jsonify({"erro": str(e)}), 400

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
