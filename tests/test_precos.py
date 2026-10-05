from datetime import datetime

import pytest

from app import db
from app.models.espaco_esportivo_model import EspacoEsportivo
from app.services import precos, validacao
from tests.conftest import auth, criar_espaco, criar_reserva, criar_usuario

SAB_E_DOM_NOITE = {"dias": [5, 6], "inicio": "18:00", "fim": "23:00", "preco_hora": 180}


def _sab(hora, minuto=0):
    return datetime(2026, 10, 10, hora, minuto)  # sábado


@pytest.fixture
def c(app, client, monkeypatch):
    # "Agora" congelado numa segunda-feira, 10:30 (horário de Brasília).
    monkeypatch.setattr(validacao, "agora", lambda: datetime(2026, 10, 5, 10, 30))
    criar_usuario("locador", "loc@t.com")
    cli = criar_usuario("locatario", "cli@t.com", cpf="11111111111")
    return {"cli_id": cli, "loc": auth(client, "loc@t.com"), "cli": auth(client, "cli@t.com")}


def _criar(client, c, regras, **extra):
    return client.post("/espacos", headers=c["loc"], json=dict(
        {"nome": "Quadra", "modalidade": "Futsal", "preco_hora": 100, "regras_preco": regras}, **extra))


def _espaco(client, c, regras):
    r = _criar(client, c, regras)
    assert r.status_code == 201, r.get_json()
    return db.session.get(EspacoEsportivo, r.get_json()["id"])


# --- cálculo ---

def test_sem_regras_vale_o_preco_padrao(client, c):
    espaco = _espaco(client, c, [])
    assert precos.preco_do_periodo(espaco, _sab(19), _sab(21)) == 200.0


def test_regra_do_horario_nobre(client, c):
    espaco = _espaco(client, c, [SAB_E_DOM_NOITE])
    assert precos.preco_do_periodo(espaco, _sab(19), _sab(21)) == 360.0


def test_periodo_que_atravessa_o_inicio_da_regra_soma_os_dois_precos(client, c):
    espaco = _espaco(client, c, [SAB_E_DOM_NOITE])
    assert precos.preco_do_periodo(espaco, _sab(17), _sab(19)) == 280.0  # 100 + 180


def test_regra_em_meia_hora_e_proporcional(client, c):
    espaco = _espaco(client, c, [{"dias": [5], "inicio": "18:30", "fim": "23:00", "preco_hora": 180}])
    assert precos.preco_do_periodo(espaco, _sab(18), _sab(19)) == 140.0  # 30 min a 100 + 30 min a 180


def test_regra_nao_vale_para_outros_dias(client, c):
    espaco = _espaco(client, c, [{"dias": [5], "inicio": "18:00", "fim": "23:00", "preco_hora": 180}])
    assert precos.preco_do_periodo(espaco, datetime(2026, 10, 9, 19), datetime(2026, 10, 9, 20)) == 100.0


# --- cadastro ---

def test_espaco_devolve_regras_agrupadas_e_faixa_de_preco(client, c):
    eid = _criar(client, c, [SAB_E_DOM_NOITE, {"dias": [0], "inicio": "08:00", "fim": "12:00", "preco_hora": 60}]).get_json()["id"]
    dados = client.get(f"/espacos/{eid}").get_json()
    assert dados["regras_preco"] == [
        {"dias": [0], "inicio": "08:00", "fim": "12:00", "preco_hora": 60.0},
        {"dias": [5, 6], "inicio": "18:00", "fim": "23:00", "preco_hora": 180.0},
    ]
    assert (dados["preco_minimo"], dados["preco_maximo"]) == (60.0, 180.0)


@pytest.mark.parametrize("regras", [
    [SAB_E_DOM_NOITE, {"dias": [6], "inicio": "22:00", "fim": "24:00", "preco_hora": 200}],  # sobrepõe no domingo
    [{"dias": [5], "inicio": "20:00", "fim": "18:00", "preco_hora": 180}],                   # fim antes do início
    [{"dias": [5], "inicio": "18:00", "fim": "23:00", "preco_hora": 0}],                     # preço inválido
    [{"dias": [], "inicio": "18:00", "fim": "23:00", "preco_hora": 180}],                    # sem dia
    [{"dias": [7], "inicio": "18:00", "fim": "23:00", "preco_hora": 180}],                   # dia inexistente
])
def test_rejeita_regras_invalidas(client, c, regras):
    assert _criar(client, c, regras).status_code == 400


def test_editar_substitui_e_lista_vazia_remove_as_regras(client, c):
    eid = _criar(client, c, [SAB_E_DOM_NOITE]).get_json()["id"]
    nova = {"dias": [2], "inicio": "10:00", "fim": "12:00", "preco_hora": 70}
    client.put(f"/espacos/{eid}", headers=c["loc"], json={"regras_preco": [nova]})
    assert client.get(f"/espacos/{eid}").get_json()["regras_preco"] == [dict(nova, preco_hora=70.0)]
    client.put(f"/espacos/{eid}", headers=c["loc"], json={"regras_preco": []})
    dados = client.get(f"/espacos/{eid}").get_json()
    assert dados["regras_preco"] == [] and dados["preco_minimo"] == dados["preco_maximo"] == 100.0


# --- reserva e agenda ---

def test_reserva_grava_o_valor_calculado(client, c):
    eid = _criar(client, c, [SAB_E_DOM_NOITE]).get_json()["id"]
    r = client.post("/reservas/realizar", headers=c["cli"], json={
        "espaco_id": eid, "data_horario": "2026-10-10T17:00", "data_fim": "2026-10-10T19:00"})
    assert r.status_code == 201
    assert r.get_json()["valor_total"] == 280.0
    minhas = client.get("/reservas", headers=c["cli"]).get_json()["reservas"]
    assert minhas[0]["valor_total"] == 280.0


def test_reserva_antiga_sem_valor_usa_o_preco_padrao(client, c):
    eid = criar_espaco(1, preco_hora=90.0)
    criar_reserva(c["cli_id"], eid, datetime(2026, 10, 6, 9), datetime(2026, 10, 6, 11))
    minhas = client.get("/reservas", headers=c["cli"]).get_json()["reservas"]
    assert minhas[0]["valor_total"] == 180.0


def test_grade_de_horarios_traz_o_preco_de_cada_hora(client, c):
    eid = _criar(client, c, [SAB_E_DOM_NOITE],
                 horarios=[{"dia_semana": 5, "abre": "16:00", "fecha": "20:00"}]).get_json()["id"]
    horarios = client.get(f"/espacos/{eid}/disponibilidade?data=2026-10-10").get_json()["horarios"]
    assert [(h["inicio"], h["preco"]) for h in horarios] == [
        ("16:00", 100.0), ("17:00", 100.0), ("18:00", 180.0), ("19:00", 180.0)]
