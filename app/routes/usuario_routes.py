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
    
    if not dados:
        return jsonify({"erro": "Nenhum dado foi enviado."}), 400
        
    try:
        # Criando o usuário usando a Factory
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

@usuario_bp.route('/usuarios/<int:id>', methods=['GET'])
def obter_usuario(id):
    """Rota para obter os detalhes de um usuário específico pelo ID."""
    usuario  = Usuario.query.get(id) # Faz basicamente um select * from usuarios where id = id
    if not usuario: # se não existir um usuário com esse ID, retorna um erro 404
        return jsonify({"erro": "Usuário não encontrado."}), 404

    dados_usuario = {
        "id": usuario.id,
        "nome": usuario.nome,
        "email": usuario.email,
        "tipo": usuario.tipo_usuario
        }
    
    # Adiciona os campos específicos de cada tipo de usuário
    if usuario.tipo_usuario == 'locatario':
        dados_usuario["cpf"] = getattr(usuario, 'cpf', None)
    elif usuario.tipo_usuario == 'locador':
        dados_usuario["cnpj"] = getattr(usuario, 'cnpj', None)
        dados_usuario["razao_social"] = getattr(usuario, 'razao_social', None)

    return jsonify(dados_usuario), 200

@usuario_bp.route('/usuarios/<int:id>', methods=['PUT'])
def atualizar_usuario(id):
    """Rota para atualizar os dados de um usuário existente."""
    usuario = Usuario.query.get(id)
    
    if not usuario:
        return jsonify({"erro": "Usuário não encontrado."}), 404

    dados = request.get_json()

    # Atualiza apenas os campos que o front-end enviou no JSON
    if 'nome' in dados:
        usuario.nome = dados['nome']
    if 'email' in dados:
        usuario.email = dados['email']
    if 'senha' in dados:
        usuario.senha = dados['senha']

    try:
        db.session.commit()
        return jsonify({"mensagem": "Usuário atualizado com sucesso!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": "Erro ao atualizar no banco.", "detalhes": str(e)}), 500


@usuario_bp.route('/usuarios/<int:id>', methods=['DELETE'])
def deletar_usuario(id):
    """Rota para excluir um usuário do sistema."""
    usuario = Usuario.query.get(id)
    
    if not usuario:
        return jsonify({"erro": "Usuário não encontrado."}), 404

    try:
        db.session.delete(usuario)
        db.session.commit()
        return jsonify({"mensagem": "Usuário excluído com sucesso!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": "Erro ao excluir. O usuário pode ter dependências.", "detalhes": str(e)}), 500