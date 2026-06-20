"""Comunicação com o backend Flask.

Único ponto do frontend que fala HTTP com a API. As telas nunca acessam o banco
diretamente: tudo passa por estas funções (Frontend Flet -> Backend Flask -> DB).
Cada função retorna a tupla `(dados: dict, status_code: int)`; `status_code == 0`
indica falha de conexão.
"""

import requests

from frontend.config import API_BASE

TIMEOUT = 8


def _resposta(r):
    """Converte a resposta em (dados, status), tolerando corpo não-JSON."""
    try:
        return r.json(), r.status_code
    except ValueError:
        return {"erro": f"Resposta inesperada do servidor (status {r.status_code})."}, r.status_code


def api_get(path):
    try:
        return _resposta(requests.get(f"{API_BASE}{path}", timeout=TIMEOUT))
    except requests.exceptions.ConnectionError:
        return {"erro": "Não foi possível conectar à API. Verifique se o backend está rodando."}, 0


def api_post(path, data):
    try:
        return _resposta(requests.post(f"{API_BASE}{path}", json=data, timeout=TIMEOUT))
    except requests.exceptions.ConnectionError:
        return {"erro": "Não foi possível conectar à API."}, 0


def api_put(path, data):
    try:
        return _resposta(requests.put(f"{API_BASE}{path}", json=data, timeout=TIMEOUT))
    except requests.exceptions.ConnectionError:
        return {"erro": "Não foi possível conectar à API."}, 0


def api_delete(path):
    try:
        return _resposta(requests.delete(f"{API_BASE}{path}", timeout=TIMEOUT))
    except requests.exceptions.ConnectionError:
        return {"erro": "Não foi possível conectar à API."}, 0


def api_login(email, senha):
    """Autentica no backend e retorna (dados_do_usuario, status)."""
    return api_post("/usuarios/login", {"email": email, "senha": senha})
