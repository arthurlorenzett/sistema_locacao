from datetime import date, datetime

import pytest

from app.services import validacao
from tests.conftest import auth, criar_espaco, criar_reserva, criar_usuario

SEGUNDA = date(2026, 10, 5)
SABADO = date(2026, 10, 10)


@pytest.fixture
def agora_fixo(monkeypatch):
    """Congela o "agora" (horário de Brasília) numa segunda-feira às 10:30."""
    monkeypatch.setattr(validacao, "agora", lambda: datetime(2026, 10, 5, 10, 30))


@pytest.fixture
def ids(app, agora_fixo):
    loc = criar_usuario("locador", "loc@t.com")
    cli = criar_usuario("locatario", "cli@t.com", cpf="11111111111")
    return {"loc": loc, "cli": cli}


def _disp(client, espaco_id, data):
    return client.get(f"/espacos/{espaco_id}/disponibilidade?data={data}")


def _horarios(resp):
    return [(h["inicio"], h["fim"], h["motivo"]) for h in resp.get_json()["horarios"]]


def test_lista_os_horarios_do_dia_de_hora_em_hora(client, ids):
    e = criar_espaco(ids["loc"], grade=[(1, "08:00", "12:00")])  # terça
    r = _disp(client, e, "2026-10-06")
    assert r.status_code == 200
    assert r.get_json()["funcionamento"] == "08:00–12:00"
    assert _horarios(r) == [("08:00", "09:00", None), ("09:00", "10:00", None),
                            ("10:00", "11:00", None), ("11:00", "12:00", None)]
    assert all(h["disponivel"] for h in r.get_json()["horarios"])


def test_horario_com_reserva_confirmada_fica_indisponivel(client, ids):
    e = criar_espaco(ids["loc"], grade=[(1, "08:00", "12:00")])
    criar_reserva(ids["cli"], e, datetime(2026, 10, 6, 9), datetime(2026, 10, 6, 11))
    criar_reserva(ids["cli"], e, datetime(2026, 10, 6, 8), status="Cancelada")
    motivos = [m for _, _, m in _horarios(_disp(client, e, "2026-10-06"))]
    assert motivos == [None, "reservado", "reservado", None]


def test_hoje_os_horarios_que_ja_comecaram_ficam_indisponiveis(client, ids):
    e = criar_espaco(ids["loc"], grade=[(0, "08:00", "12:00")])
    motivos = [m for _, _, m in _horarios(_disp(client, e, SEGUNDA))]
    assert motivos == ["passado", "passado", "passado", None]


def test_dia_fechado_nao_tem_horarios(client, ids):
    e = criar_espaco(ids["loc"], grade=[(1, "08:00", "12:00")])
    r = _disp(client, e, "2026-10-07")  # quarta
    assert r.get_json()["funcionamento"] is None
    assert r.get_json()["horarios"] == []


def test_espaco_que_fecha_a_meia_noite(client, ids):
    e = criar_espaco(ids["loc"], grade=[(5, "21:00", "24:00")])
    assert _horarios(_disp(client, e, SABADO))[-1] == ("23:00", "24:00", None)


def test_espaco_sem_grade_usa_janela_padrao_das_8_as_22(client, ids):
    e = criar_espaco(ids["loc"])
    h = _horarios(_disp(client, e, "2026-10-06"))
    assert (h[0][0], h[-1][1], len(h)) == ("08:00", "22:00", 14)


def test_data_invalida_e_espaco_inexistente(client, ids):
    e = criar_espaco(ids["loc"])
    assert _disp(client, e, "06/10/2026").status_code == 400
    assert _disp(client, 999, "2026-10-06").status_code == 404


# --- catálogo ---

def test_catalogo_informa_e_filtra_quem_tem_horario_livre_hoje(client, ids):
    livre = criar_espaco(ids["loc"], nome="Livre", grade=[(0, "08:00", "22:00")])
    fechada_hoje = criar_espaco(ids["loc"], nome="Fechada", grade=[(1, "08:00", "22:00")])
    lotada = criar_espaco(ids["loc"], nome="Lotada", grade=[(0, "08:00", "12:00")])
    criar_reserva(ids["cli"], lotada, datetime(2026, 10, 5, 11), datetime(2026, 10, 5, 12))

    catalogo = {e["id"]: e["livre_hoje"] for e in client.get("/espacos").get_json()["espacos"]}
    assert catalogo == {livre: True, fechada_hoje: False, lotada: False}

    filtrado = [e["id"] for e in client.get("/espacos?disponivel_hoje=1").get_json()["espacos"]]
    assert filtrado == [livre]


# --- reserva usa a mesma regra da agenda ---

def test_reserva_de_duas_horas_que_atravessa_horario_reservado_e_recusada(client, ids):
    e = criar_espaco(ids["loc"], grade=[(1, "08:00", "12:00")])
    criar_reserva(ids["cli"], e, datetime(2026, 10, 6, 10), datetime(2026, 10, 6, 11))
    cli = auth(client, "cli@t.com")
    r = client.post("/reservas/realizar", headers=cli, json={
        "espaco_id": e, "data_horario": "2026-10-06T09:00", "data_fim": "2026-10-06T11:00"})
    assert r.status_code == 400
    assert "confirmada" in r.get_json()["erro"]
    ok = client.post("/reservas/realizar", headers=cli, json={
        "espaco_id": e, "data_horario": "2026-10-06T08:00", "data_fim": "2026-10-06T10:00"})
    assert ok.status_code == 201
