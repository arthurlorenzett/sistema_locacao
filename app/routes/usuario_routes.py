from flask import Blueprint, request, jsonify
from app.factories.usuario_factory import UsuarioFactory
from app import db

# Cria um agrupamento de rotas para usuários
usuario_bp = Blueprint('usuario_bp', __name__)

@usuario_bp.route('/cadastrar', methods=['POST'])
def cadastrar_usuario():
    """
    Endpoint para cadastrar novos usuários.
    Espera receber um JSON com os dados do usuário.
    """
    dados = request.get_json()
    
    try:
        # A criação de usuários é centralizada pela UsuarioFactory, 
        # reduzindo o acoplamento das rotas da API com classes concretas[cite: 175].
        novo_usuario = UsuarioFactory.criar_usuario(
            tipo=dados.get('tipo'),
            nome=dados.get('nome'),
            email=dados.get('email'),
            senha=dados.get('senha'),
            cpf=dados.get('cpf'),
            cnpj=dados.get('cnpj'),
            razao_social=dados.get('razao_social')
        )
        
        # Salva o novo objeto no banco de dados PostgreSQL 
        db.session.add(novo_usuario)
        db.session.commit()
        
        return jsonify({"mensagem": f"Usuário do tipo '{dados.get('tipo')}' cadastrado com sucesso!"}), 201
        
    except ValueError as e:
        # Captura os erros gerados pela validação da Factory (ex: CPF faltando)
        return jsonify({"erro": str(e)}), 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": "Erro interno no servidor."}), 500