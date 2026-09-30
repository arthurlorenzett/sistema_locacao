"""Comunicação com o backend Flask.

Único ponto do frontend que fala HTTP com a API. As telas nunca acessam o banco
diretamente: tudo passa por estas funções (Frontend Flet -> Backend Flask -> DB).
Cada função retorna a tupla `(dados: dict, status_code: int)`; `status_code == 0`
indica falha de conexão.

O token é lido da sessão da página Flet atual (`ft.context.page`) e enviado no
header `Authorization: Bearer`. Ele NÃO pode ficar em variável global: no modo
web um único processo Python atende todos os navegadores, e um token global faria
um usuário herdar a sessão do último que fez login.
"""

from urllib.parse import urlencode

import flet as ft
import requests

from frontend.config import API_BASE
from frontend.sessao import obter_token

# Generoso porque o backend no plano free do Render "dorme" e leva ~1 min para acordar.
TIMEOUT = 60

_ERRO_CONEXAO = "Não foi possível conectar à API. Verifique se o backend está rodando."
_ERRO_TIMEOUT = "O servidor demorou demais para responder. Tente novamente em instantes."


def _headers():
    try:
        token = obter_token(ft.context.page)
    except RuntimeError:  # fora de um callback Flet (ex.: scripts/testes)
        token = None
    return {"Authorization": f"Bearer {token}"} if token else {}


def _resposta(r):
    """Converte a resposta em (dados, status), tolerando corpo não-JSON."""
    try:
        return r.json(), r.status_code
    except ValueError:
        return {"erro": f"Resposta inesperada do servidor (status {r.status_code})."}, r.status_code


def _requisitar(metodo, path, data=None):
    try:
        r = requests.request(metodo, f"{API_BASE}{path}", json=data,
                             headers=_headers(), timeout=TIMEOUT)
    except requests.exceptions.Timeout:
        return {"erro": _ERRO_TIMEOUT}, 0
    except requests.exceptions.RequestException:
        return {"erro": _ERRO_CONEXAO}, 0
    return _resposta(r)


def api_get(path):
    return _requisitar("GET", path)


def api_post(path, data):
    return _requisitar("POST", path, data)


def api_put(path, data):
    return _requisitar("PUT", path, data)


def api_delete(path):
    return _requisitar("DELETE", path)


# --- Autenticação ---

def api_login(email, senha):
    """Autentica no backend e retorna (dados_do_usuario, status)."""
    return api_post("/usuarios/login", {"email": email, "senha": senha})


# --- Espaços esportivos ---

def api_listar_espacos(filtros=None):
    """Lista espaços do catálogo aplicando filtros (dict) como query string."""
    filtros = {k: v for k, v in (filtros or {}).items() if v not in (None, "")}
    qs = f"?{urlencode(filtros)}" if filtros else ""
    return api_get(f"/espacos{qs}")


def api_meus_espacos():
    return api_get("/espacos/meus")


def api_espaco(id):
    return api_get(f"/espacos/{id}")


def api_disponibilidade(espaco_id, data):
    """Horários do dia (data AAAA-MM-DD) com o que está livre para reservar."""
    return api_get(f"/espacos/{espaco_id}/disponibilidade?data={data}")


def api_criar_espaco(dados):
    return api_post("/espacos", dados)


def api_editar_espaco(id, dados):
    return api_put(f"/espacos/{id}", dados)


def api_desativar_espaco(id):
    return api_delete(f"/espacos/{id}")


# --- Favoritos ---

def api_favoritos():
    return api_get("/favoritos")


def api_favoritar(espaco_id):
    return api_post(f"/favoritos/{espaco_id}", {})


def api_desfavoritar(espaco_id):
    return api_delete(f"/favoritos/{espaco_id}")


# --- Reservas ---

def api_reservar(espaco_id, data_horario, data_fim=None):
    return api_post("/reservas/realizar", {
        "espaco_id": espaco_id,
        "data_horario": data_horario,
        "data_fim": data_fim,
    })


def api_minhas_reservas():
    return api_get("/reservas")


def api_reservas_recebidas():
    return api_get("/reservas/recebidas")


def api_confirmar_reserva(id, metodo_pagamento):
    return api_put(f"/reservas/{id}/confirmar", {"metodo_pagamento": metodo_pagamento})


def api_cancelar_reserva(id):
    return api_put(f"/reservas/{id}/cancelar", {})
