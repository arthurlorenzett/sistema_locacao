from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError # Importação nova para capturar erro de exclusão
from app.factories.usuario_factory import UsuarioFactory
from app.models.usuario_model import Usuario 
from app import db

usuario_bp = Blueprint('usuario_bp', __name__)

@usuario_bp.route('', methods=['POST'], strict_slashes=False)
def cadastrar_usuario():
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

@usuario_bp.route('', methods=['GET'], strict_slashes=False)
def listar_usuarios():
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
    usuario = Usuario.query.get(id)
    if not usuario:
        return jsonify({"erro": "Usuário não encontrado."}), 404
        
    dados = {
        "id": usuario.id,
        "nome": usuario.nome,
        "email": usuario.email,
        "tipo": usuario.tipo_usuario
    }
    
    if usuario.tipo_usuario == 'locatario':
        dados['cpf'] = usuario.cpf
    elif usuario.tipo_usuario == 'locador':
        dados['cnpj'] = usuario.cnpj
        dados['razao_social'] = usuario.razao_social
        
    return jsonify(dados), 200

@usuario_bp.route('/<int:id>', methods=['PUT'])
def editar_usuario(id):
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
    usuario = Usuario.query.get(id)
    if not usuario:
        return jsonify({"erro": "Usuário não encontrado."}), 404
        
    try:
        db.session.delete(usuario)
        db.session.commit()
        return jsonify({"mensagem": "Usuário deletado."}), 200
    except IntegrityError:
        # Se o banco chiar porque o usuário tem quadras ou reservas, cai aqui!
        db.session.rollback()
        return jsonify({
            "erro": "Não é possível excluir este usuário pois ele possui reservas ou espaços esportivos vinculados."
        }), 409 # 409 Conflict