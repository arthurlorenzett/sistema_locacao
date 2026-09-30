"""O token de autenticação deve ser isolado por sessão (página) do Flet.

No modo web um único processo atende todos os navegadores: se o token fosse
global, um usuário passaria a usar a sessão do último que fez login.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app", "views"))

from flet.controls import context as flet_context  # noqa: E402

from frontend import api_client  # noqa: E402


class _Store(dict):
    def set(self, k, v):
        self[k] = v


class _Session:
    def __init__(self):
        self.store = _Store()


class _PaginaFalsa:
    def __init__(self, token=None):
        self.session = _Session()
        if token:
            self.session.store.set("token", token)


def _headers_na_pagina(pagina):
    ctx = flet_context._context_page.set(pagina)
    try:
        return api_client._headers()
    finally:
        flet_context._context_page.reset(ctx)


def test_token_isolado_por_sessao():
    assert _headers_na_pagina(_PaginaFalsa("token-A")) == {"Authorization": "Bearer token-A"}
    assert _headers_na_pagina(_PaginaFalsa("token-B")) == {"Authorization": "Bearer token-B"}
    assert _headers_na_pagina(_PaginaFalsa()) == {}


def test_sem_pagina_nao_envia_token():
    assert api_client._headers() == {}
