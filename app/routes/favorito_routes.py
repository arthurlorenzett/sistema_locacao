"""Rotas de favoritos: o locatário guarda espaços para acesso rápido."""

from flask import Blueprint, jsonify, g

from app import db
from app.models.espaco_esportivo_model import EspacoEsportivo
from app.models.favorito_model import Favorito
from app.auth.decorators import requer_perfil
from app.services.catalogo import dict_catalogo

favorito_bp = Blueprint('favorito_bp', __name__)


@favorito_bp.route('', methods=['GET'], strict_slashes=False)
@requer_perfil('locatario')
def listar_favoritos():
    espacos = (EspacoEsportivo.query
               .join(Favorito, Favorito.espaco_id == EspacoEsportivo.id)
               .filter(Favorito.locatario_id == g.usuario.id, EspacoEsportivo.ativo.is_(True))
               .order_by(Favorito.created_at.desc())
               .all())
    todos = {e.id for e in espacos}
    return jsonify({"espacos": [dict_catalogo(e, todos) for e in espacos],
                    "total": len(espacos)}), 200


@favorito_bp.route('/<int:espaco_id>', methods=['POST'])
@requer_perfil('locatario')
def favoritar(espaco_id):
    if not EspacoEsportivo.query.get(espaco_id):
        return jsonify({"erro": "Espaço não encontrado."}), 404

    if Favorito.query.filter_by(locatario_id=g.usuario.id, espaco_id=espaco_id).first():
        return jsonify({"mensagem": "Espaço já está nos favoritos."}), 200

    db.session.add(Favorito(locatario_id=g.usuario.id, espaco_id=espaco_id))
    db.session.commit()
    return jsonify({"mensagem": "Adicionado aos favoritos."}), 201


@favorito_bp.route('/<int:espaco_id>', methods=['DELETE'])
@requer_perfil('locatario')
def desfavoritar(espaco_id):
    Favorito.query.filter_by(locatario_id=g.usuario.id, espaco_id=espaco_id).delete()
    db.session.commit()
    return jsonify({"mensagem": "Removido dos favoritos."}), 200
