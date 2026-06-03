from flask import Blueprint, jsonify

main_bp = Blueprint('main_bp', __name__)

@main_bp.route('/', methods=['GET'])
def pagina_inicial():
    return jsonify({
        "status": "online",
        "projeto": "Sistema de Gestão e Locação de Espaços Esportivos",
        "versao": "1.0.0",
        "mensagem": "Bem-vindo ao backend do projeto! A API está operando normalmente.",
        "endpoints_disponiveis": {
            "listar_usuarios": "GET /usuarios"
        }
    }), 200