"""Decorators de proteção de rotas (RBAC).

`login_obrigatorio` exige um token válido; `requer_perfil(*perfis)` exige, além
disso, que o usuário tenha um dos perfis informados. Em ambos os casos o usuário
autenticado fica disponível em `flask.g.usuario`.
"""

from functools import wraps

from flask import request, jsonify, g

from app.auth.seguranca import verificar_token
from app.models.usuario_model import Usuario


def _usuario_do_token():
    """Lê o header Authorization, valida o token e devolve (usuario, erro_response, status)."""
    cabecalho = request.headers.get("Authorization", "")
    if not cabecalho.startswith("Bearer "):
        return None, jsonify({"erro": "Autenticação necessária."}), 401

    token = cabecalho[len("Bearer "):].strip()
    payload = verificar_token(token)
    if not payload:
        return None, jsonify({"erro": "Sessão inválida ou expirada."}), 401

    usuario = Usuario.query.get(payload.get("id"))
    if not usuario:
        return None, jsonify({"erro": "Usuário não encontrado."}), 401
    if not getattr(usuario, "ativo", True):
        return None, jsonify({"erro": "Usuário bloqueado."}), 403

    return usuario, None, None


def login_obrigatorio(func):
    """Garante que há um usuário autenticado válido."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        usuario, erro, status = _usuario_do_token()
        if erro is not None:
            return erro, status
        g.usuario = usuario
        return func(*args, **kwargs)
    return wrapper


def requer_perfil(*perfis):
    """Garante que o usuário autenticado tem um dos perfis informados."""
    def decorador(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            usuario, erro, status = _usuario_do_token()
            if erro is not None:
                return erro, status
            if usuario.tipo_usuario not in perfis:
                return jsonify({"erro": "Você não tem permissão para esta ação."}), 403
            g.usuario = usuario
            return func(*args, **kwargs)
        return wrapper
    return decorador
