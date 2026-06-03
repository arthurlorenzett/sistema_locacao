from flask import Blueprint, jsonify, request
from app.models.usuario_model import Usuario
from app.factories.usuario_factory import UsuarioFactory
from app import db

""" Criando o "Blueprint" (um agrupador de rotas para organizar o projeto)"""
usuario_bp = Blueprint('usuario_bp', __name__)

@usuario_bp.route('/usuarios', methods=['GET'])
def listar_usuarios():
    """Rota para listar todos os usuários cadastrados."""
    # Busca todos os usuários no banco de dados
    usuarios = Usuario.query.all()
    lista_usuarios = [{"id": u.id, "nome": u.nome, "tipo": u.tipo_usuario} for u in usuarios]
    return jsonify({
        "mensagem": "Sucesso! A rota de usuários está funcionando perfeitamente.",
        "total_usuarios": len(usuarios),
        "usuarios": lista_usuarios
    }), 200
    
@usuario_bp.route('/usuarios', methods=['POST'])
def criar_usuario():
    """Rota para cadastrar um novo usuário no sistema."""
    # Pegando os dados que chegaram na requisição
    dados = request.get_json()
    
    # Evita que o sistema quebre se alguém mandar uma requisição vazia
    if not dados:
        return jsonify({"erro": "Nenhum dado foi enviado."}), 400
        
    try:
        # Aqui a mágica acontece: Passamos a bola para a Factory!
        novo_usuario = UsuarioFactory.criar_usuario(
            tipo=dados.get('tipo'),
            nome=dados.get('nome'),
            email=dados.get('email'),
            senha=dados.get('senha'),
            cpf=dados.get('cpf'),
            cnpj=dados.get('cnpj'),
            razao_social=dados.get('razao_social')
        )
        
        # Salva o objeto criado no banco de dados
        db.session.add(novo_usuario)
        db.session.commit()
        
        return jsonify({
            "mensagem": f"{dados.get('tipo').capitalize()} cadastrado com sucesso!",
            "id_usuario": novo_usuario.id
        }), 201
        
    except ValueError as erro: # Captura os erros de validação da Factory (ex: tipo desconhecido, falta de CPF para locatário, etc)
        return jsonify({"erro": str(erro)}), 400
    except Exception as e:
        # Prevenção extra caso o banco de dados dê algum erro (ex: email repetido)
        db.session.rollback() 
        return jsonify({"erro": "Erro ao salvar no banco de dados.", "detalhes": str(e)}), 500