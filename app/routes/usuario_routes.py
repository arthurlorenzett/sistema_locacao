from flask import Blueprint, jsonify
from app.models.usuario_model import Usuario

""" Criando o "Blueprint" (um agrupador de rotas para organizar o projeto)"""
usuario_bp = Blueprint('usuario_bp', __name__)

@usuario_bp.route('/usuarios', methods=['GET'])
def listar_usuarios():
    """Rota para listar todos os usuários cadastrados."""
    # Busca todos os usuários no banco de dados
    usuarios = Usuario.query.all()
    return jsonify({
        "mensagem": "Sucesso! A rota de usuários está funcionando perfeitamente.",
        "total_usuarios": len(usuarios)
    }), 200