from datetime import datetime

import pytest

from app.services import validacao
from tests.conftest import auth, criar_espaco, criar_reserva, criar_usuario

TERCA = "2026-10-06"


@pytest.fixture
def cenario(app, client, monkeypatch):
    # "Agora" congelado numa segunda-feira, 10:30 (horário de Brasília).
    monkeypatch.setattr(validacao, "agora", lambda: datetime(2026, 10, 5, 10, 30))
    loc = criar_usuario("locador", "loc@t.com")
    criar_usuario("locador", "outro@t.com", cnpj="99999999999999")
    cli = criar_usuario("locatario", "cli@t.com", cpf="11111111111")
    espaco = criar_espaco(loc, grade=[(d, "08:00", "12:00") for d in range(7)])
    return {"espaco": espaco, "cli_id": cli, "loc": auth(client, "loc@t.com"),
            "cli": auth(client, "cli@t.com"), "outro": auth(client, "outro@t.com")}


def _bloquear(client, c, headers=None, **dados):
    return client.post(f"/espacos/{c['espaco']}/bloqueios", headers=headers or c["loc"], json=dados)


def _motivos(client, c, data=TERCA):
    r = client.get(f"/espacos/{c['espaco']}/disponibilidade?data={data}")
    return [h["motivo"] for h in r.get_json()["horarios"]]


# --- cadastro ---

def test_dono_bloqueia_uma_faixa_e_ve_na_lista(client, cenario):
    r = _bloquear(client, cenario, inicio=f"{TERCA}T09:00", fim=f"{TERCA}T11:00", motivo="Manutenção")
    assert r.status_code == 201
    lista = client.get(f"/espacos/{cenario['espaco']}/bloqueios", headers=cenario["loc"]).get_json()
    assert [(b["inicio"], b["fim"], b["motivo"]) for b in lista["bloqueios"]] == [
        ("2026-10-06T09:00:00", "2026-10-06T11:00:00", "Manutenção")]


def test_bloqueio_de_dia_inteiro(client, cenario):
    assert _bloquear(client, cenario, data=TERCA, dia_inteiro=True).status_code == 201
    b = client.get(f"/espacos/{cenario['espaco']}/bloqueios", headers=cenario["loc"]).get_json()["bloqueios"][0]
    assert (b["inicio"], b["fim"]) == ("2026-10-06T00:00:00", "2026-10-07T00:00:00")


def test_so_o_dono_gerencia_bloqueios(client, cenario):
    dados = {"data": TERCA, "dia_inteiro": True}
    assert client.post(f"/espacos/{cenario['espaco']}/bloqueios", json=dados).status_code == 401
    assert _bloquear(client, cenario, headers=cenario["cli"], **dados).status_code == 403
    assert _bloquear(client, cenario, headers=cenario["outro"], **dados).status_code == 403
    assert client.get(f"/espacos/{cenario['espaco']}/bloqueios", headers=cenario["outro"]).status_code == 403


@pytest.mark.parametrize("dados", [
    {"inicio": f"{TERCA}T11:00", "fim": f"{TERCA}T09:00"},        # fim antes do início
    {"inicio": "2026-10-05T08:00", "fim": "2026-10-05T10:00"},    # já passou
    {"data": "05/10/2026", "dia_inteiro": True},                  # data inválida
    {"inicio": f"{TERCA}T09:00"},                                 # sem fim
])
def test_rejeita_bloqueio_invalido(client, cenario, dados):
    assert _bloquear(client, cenario, **dados).status_code == 400


def test_nao_bloqueia_periodo_com_reserva(client, cenario):
    criar_reserva(cenario["cli_id"], cenario["espaco"], datetime(2026, 10, 6, 10), status="Pendente")
    r = _bloquear(client, cenario, data=TERCA, dia_inteiro=True)
    assert r.status_code == 409
    assert "reserva" in r.get_json()["erro"]


# --- efeito na agenda ---

def test_horarios_bloqueados_somem_da_grade_do_cliente(client, cenario):
    _bloquear(client, cenario, inicio=f"{TERCA}T09:00", fim=f"{TERCA}T11:00", motivo="Particular")
    assert _motivos(client, cenario) == [None, "bloqueado", "bloqueado", None]
    # o motivo é interno do locador: não vai para a grade pública
    horarios = client.get(f"/espacos/{cenario['espaco']}/disponibilidade?data={TERCA}").get_json()["horarios"]
    assert "Particular" not in str(horarios)


def test_reserva_em_horario_bloqueado_e_recusada(client, cenario):
    _bloquear(client, cenario, data=TERCA, dia_inteiro=True)
    r = client.post("/reservas/realizar", headers=cenario["cli"], json={
        "espaco_id": cenario["espaco"], "data_horario": f"{TERCA}T09:00"})
    assert r.status_code == 400
    assert "bloqueado" in r.get_json()["erro"]


def test_busca_por_data_e_hora_esconde_espaco_bloqueado(client, cenario):
    _bloquear(client, cenario, data=TERCA, dia_inteiro=True)
    ids = [e["id"] for e in client.get(f"/espacos?data={TERCA}&hora=09:00").get_json()["espacos"]]
    assert cenario["espaco"] not in ids


def test_remover_bloqueio_libera_os_horarios(client, cenario):
    bid = _bloquear(client, cenario, data=TERCA, dia_inteiro=True).get_json()["id"]
    assert client.delete(f"/espacos/{cenario['espaco']}/bloqueios/{bid}",
                         headers=cenario["outro"]).status_code == 403
    assert client.delete(f"/espacos/{cenario['espaco']}/bloqueios/{bid}",
                         headers=cenario["loc"]).status_code == 200
    assert _motivos(client, cenario) == [None, None, None, None]
