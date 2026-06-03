"""
Módulo de rotas base e testes da aplicação.
Contém os endpoints iniciais para validação do servidor.
"""

from flask import Blueprint, jsonify

# Cria o Blueprint para rotas base
base_bp = Blueprint('base_bp', __name__)

@base_bp.route('/', methods=['GET'])
def pagina_inicial():
    """
    Rota inicial padrão (Home).
    Retorna uma mensagem JSON confirmando que o backend está online.
    """
    return jsonify({
        "status": "online",
        "mensagem": "Backend do Sistema de Locação Esportiva funcionando perfeitamente!"
    }), 200