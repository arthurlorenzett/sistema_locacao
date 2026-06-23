"""Geração e validação de tokens de sessão.

Usa `itsdangerous.URLSafeTimedSerializer` (assinatura HMAC com a SECRET_KEY do app).
O token é stateless: carrega o id e o tipo do usuário e tem validade temporal.
"""

from typing import Optional

from flask import current_app
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

# Namespace de assinatura (evita reaproveitar tokens entre finalidades distintas).
_SALT = "arena-facil-auth"

# Validade padrão do token: 7 dias (em segundos).
VALIDADE_PADRAO = 7 * 24 * 60 * 60


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt=_SALT)


def gerar_token(usuario) -> str:
    """Gera um token assinado para o usuário autenticado."""
    return _serializer().dumps({"id": usuario.id, "tipo_usuario": usuario.tipo_usuario})


def verificar_token(token: str, max_age: int = VALIDADE_PADRAO) -> Optional[dict]:
    """Valida o token e devolve o payload (`{id, tipo_usuario}`) ou None se inválido/expirado."""
    if not token:
        return None
    try:
        return _serializer().loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None
