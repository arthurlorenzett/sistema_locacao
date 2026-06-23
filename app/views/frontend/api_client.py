"""Comunicação com o backend Flask.

Único ponto do frontend que fala HTTP com a API. As telas nunca acessam o banco
diretamente: tudo passa por estas funções (Frontend Flet -> Backend Flask -> DB).
Cada função retorna a tupla `(dados: dict, status_code: int)`; `status_code == 0`
indica falha de conexão.

O token de sessão é mantido em nível de módulo (`definir_token`/`limpar_token`)
e enviado automaticamente no header `Authorization: Bearer` das requisições.
"""

from urllib.parse import urlencode

import requests

from frontend.config import API_BASE

TIMEOUT = 60

# Token de autenticação atual (definido após o login).
_TOKEN = None


def definir_token(token):
    global _TOKEN
    _TOKEN = token


def limpar_token():
    global _TOKEN
    _TOKEN = None


def _headers():
    return {"Authorization": f"Bearer {_TOKEN}"} if _TOKEN else {}


def _resposta(r):
    """Converte a resposta em (dados, status), tolerando corpo não-JSON."""
    try:
        return r.json(), r.status_code
    except ValueError:
        return {"erro": f"Resposta inesperada do servidor (status {r.status_code})."}, r.status_code


def api_get(path):
    try:
        return _resposta(requests.get(f"{API_BASE}{path}", headers=_headers(), timeout=TIMEOUT))
    except requests.exceptions.ConnectionError:
        return {"erro": "Não foi possível conectar à API. Verifique se o backend está rodando."}, 0


def api_post(path, data):
    try:
        return _resposta(requests.post(f"{API_BASE}{path}", json=data, headers=_headers(), timeout=TIMEOUT))
    except requests.exceptions.ConnectionError:
        return {"erro": "Não foi possível conectar à API."}, 0


def api_put(path, data):
    try:
        return _resposta(requests.put(f"{API_BASE}{path}", json=data, headers=_headers(), timeout=TIMEOUT))
    except requests.exceptions.ConnectionError:
        return {"erro": "Não foi possível conectar à API."}, 0


def api_delete(path):
    try:
        return _resposta(requests.delete(f"{API_BASE}{path}", headers=_headers(), timeout=TIMEOUT))
    except requests.exceptions.ConnectionError:
        return {"erro": "Não foi possível conectar à API."}, 0


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


def api_criar_espaco(dados):
    return api_post("/espacos", dados)


def api_editar_espaco(id, dados):
    return api_put(f"/espacos/{id}", dados)


def api_desativar_espaco(id):
    return api_delete(f"/espacos/{id}")


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
