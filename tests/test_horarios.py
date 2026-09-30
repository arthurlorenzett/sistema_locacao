from datetime import timedelta

import pytest

from app.services import validacao
from tests.conftest import auth, criar_espaco, criar_usuario

SEG_08_22 = {"dia_semana": 0, "abre": "08:00", "fecha": "22:00"}
SAB_09_24 = {"dia_semana": 5, "abre": "09:00", "fecha": "24:00"}


def _proximo(dia_semana):
    """Próxima data (a partir de amanhã) no dia da semana informado (0 = segunda)."""
    hoje = validacao.agora().date()
    return hoje + timedelta(days=(dia_semana - hoje.weekday() - 1) % 7 + 1)


@pytest.fixture
def cenario(app, client):
    criar_usuario("locador", "loc@t.com")
    criar_usuario("locatario", "cli@t.com", cpf="11111111111")
    loc = auth(client, "loc@t.com")
    r = client.post("/espacos", headers=loc, json={
        "nome": "Quadra", "modalidade": "Futsal", "preco_hora": 100,
        "horarios": [SEG_08_22, SAB_09_24],
    })
    assert r.status_code == 201, r.get_json()
    return {"espaco": r.get_json()["id"], "loc": loc, "cli": auth(client, "cli@t.com")}


def _reservar(client, cenario, data, hora):
    return client.post("/reservas/realizar", headers=cenario["cli"], json={
        "espaco_id": cenario["espaco"], "data_horario": f"{data}T{hora}"})


# --- cadastro ---

def test_espaco_devolve_horarios_cadastrados(client, cenario):
    horarios = client.get(f"/espacos/{cenario['espaco']}").get_json()["horarios"]
    assert horarios == [SEG_08_22, SAB_09_24]


@pytest.mark.parametrize("horarios", [
    [],                                                     # nenhum dia
    [{"dia_semana": 0, "abre": "22:00", "fecha": "08:00"}],  # fecha antes de abrir
    [{"dia_semana": 0, "abre": "08:00", "fecha": "25:00"}],  # hora inexistente
    [{"dia_semana": 7, "abre": "08:00", "fecha": "22:00"}],  # dia inexistente
    [SEG_08_22, SEG_08_22],                                 # dia repetido
])
def test_rejeita_horarios_invalidos(client, cenario, horarios):
    r = client.post("/espacos", headers=cenario["loc"], json={
        "nome": "X", "modalidade": "Futsal", "preco_hora": 50, "horarios": horarios})
    assert r.status_code == 400


def test_editar_substitui_horarios(client, cenario):
    novo = {"dia_semana": 2, "abre": "10:00", "fecha": "18:30"}
    r = client.put(f"/espacos/{cenario['espaco']}", headers=cenario["loc"], json={"horarios": [novo]})
    assert r.status_code == 200
    assert client.get(f"/espacos/{cenario['espaco']}").get_json()["horarios"] == [novo]


# --- reservas ---

def test_reserva_dentro_do_horario(client, cenario):
    assert _reservar(client, cenario, _proximo(0), "21:00").status_code == 201


def test_reserva_antes_de_abrir_e_recusada(client, cenario):
    r = _reservar(client, cenario, _proximo(0), "07:00")
    assert r.status_code == 400
    assert "08:00–22:00" in r.get_json()["erro"]


def test_reserva_que_termina_depois_de_fechar_e_recusada(client, cenario):
    assert _reservar(client, cenario, _proximo(0), "21:30").status_code == 400


def test_reserva_em_dia_fechado_e_recusada(client, cenario):
    r = _reservar(client, cenario, _proximo(1), "10:00")
    assert r.status_code == 400
    assert "fechado" in r.get_json()["erro"]


def test_reserva_ate_meia_noite(client, cenario):
    assert _reservar(client, cenario, _proximo(5), "23:00").status_code == 201


def test_espaco_sem_horario_cadastrado_aceita_qualquer_hora(client, cenario):
    antigo = criar_espaco(1)  # criado sem horários (como os espaços anteriores à funcionalidade)
    r = client.post("/reservas/realizar", headers=cenario["cli"], json={
        "espaco_id": antigo, "data_horario": f"{_proximo(1)}T03:00"})
    assert r.status_code == 201


# --- busca ---

def test_busca_por_data_e_hora_esconde_espaco_fechado(client, cenario):
    segunda = _proximo(0)
    ids = lambda hora: [e["id"] for e in client.get(f"/espacos?data={segunda}&hora={hora}").get_json()["espacos"]]
    assert cenario["espaco"] not in ids("07:00")
    assert cenario["espaco"] in ids("09:00")
