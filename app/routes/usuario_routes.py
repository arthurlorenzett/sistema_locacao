from flask import Blueprint, request, jsonify
from app.factories.usuario_factory import UsuarioFactory
from app.models.usuario_model import Usuario # Importando a classe mãe
from app import db

usuario_bp = Blueprint('usuario_bp', __name__)

@usuario_bp.route('/', methods=['POST'])
def cadastrar_usuario():
    """Cria um novo usuário (usado pela tela_cadastro do Flet)"""
    dados = request.get_json()
    try:
        novo_usuario = UsuarioFactory.criar_usuario(
            tipo=dados.get('tipo'),
            nome=dados.get('nome'),
            email=dados.get('email'),
            senha=dados.get('senha'),
            cpf=dados.get('cpf'),
            cnpj=dados.get('cnpj'),
            razao_social=dados.get('razao_social')
        )
        db.session.add(novo_usuario)
        db.session.commit()
        return jsonify({"mensagem": f"Usuário '{dados.get('nome')}' cadastrado com sucesso!"}), 201
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": "Erro interno no servidor."}), 500

@usuario_bp.route('/', methods=['GET'])
def listar_usuarios():
    """Lista todos os usuários (usado pela tela_usuarios do Flet)"""
    usuarios = Usuario.query.all()
    lista = []
    for u in usuarios:
        lista.append({
            "id": u.id,
            "nome": u.nome,
            "email": u.email,
            "tipo": u.tipo_usuario
        })
    return jsonify({"usuarios": lista, "total_usuarios": len(lista)}), 200

@usuario_bp.route('/<int:id>', methods=['GET'])
def detalhar_usuario(id):
    """Busca os detalhes completos de um usuário específico"""
    usuario = Usuario.query.get(id)
    if not usuario:
        return jsonify({"erro": "Usuário não encontrado."}), 404
        
    dados = {
        "id": usuario.id,
        "nome": usuario.nome,
        "email": usuario.email,
        "tipo": usuario.tipo_usuario
    }
    
    # Adiciona os campos específicos dependendo do tipo usando o Polimorfismo
    if usuario.tipo_usuario == 'locatario':
        dados['cpf'] = usuario.cpf
    elif usuario.tipo_usuario == 'locador':
        dados['cnpj'] = usuario.cnpj
        dados['razao_social'] = usuario.razao_social
        
    return jsonify(dados), 200

@usuario_bp.route('/<int:id>', methods=['PUT'])
def editar_usuario(id):
    """Atualiza um usuário existente (usado pela tela_editar do Flet)"""
    usuario = Usuario.query.get(id)
    if not usuario:
        return jsonify({"erro": "Usuário não encontrado."}), 404
        
    dados = request.get_json()
    if 'nome' in dados:
        usuario.nome = dados['nome']
    if 'email' in dados:
        usuario.email = dados['email']
    if 'senha' in dados:
        usuario.senha = dados['senha']
        
    db.session.commit()
    return jsonify({"mensagem": "Usuário atualizado com sucesso!"}), 200

@usuario_bp.route('/<int:id>', methods=['DELETE'])
def deletar_usuario(id):
    """Deleta um usuário (usado pelo botão de lixeira no Flet)"""
    usuario = Usuario.query.get(id)
    if not usuario:
        return jsonify({"erro": "Usuário não encontrado."}), 404
        
    db.session.delete(usuario)
    db.session.commit()
    return jsonify({"mensagem": "Usuário deletado."}), 200