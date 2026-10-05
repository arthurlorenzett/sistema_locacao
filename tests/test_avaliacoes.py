from datetime import datetime

import pytest

from app.services import validacao
from tests.conftest import auth, criar_espaco, criar_reserva, criar_usuario

ONTEM = datetime(2026, 10, 4, 9)
AMANHA = datetime(2026, 10, 6, 9)


@pytest.fixture
def c(app, client, monkeypatch):
    # "Agora" congelado numa segunda-feira, 10:30 (horário de Brasília).
    monkeypatch.setattr(validacao, "agora", lambda: datetime(2026, 10, 5, 10, 30))
    loc = criar_usuario("locador", "loc@t.com")
    cli = criar_usuario("locatario", "cli@t.com", cpf="11111111111", nome="João Silva")
    outro = criar_usuario("locatario", "outro@t.com", cpf="22222222222", nome="Maria Souza")
    espaco = criar_espaco(loc)
    return {"espaco": espaco, "cli_id": cli, "outro_id": outro, "loc": auth(client, "loc@t.com"),
            "cli": auth(client, "cli@t.com"), "outro": auth(client, "outro@t.com")}


def _avaliar(client, headers, reserva_id, nota=5, comentario=None):
    return client.post(f"/reservas/{reserva_id}/avaliacao", headers=headers,
                       json={"nota": nota, "comentario": comentario})


# --- quem pode avaliar ---

def test_cliente_avalia_reserva_ja_realizada(client, c):
    rid = criar_reserva(c["cli_id"], c["espaco"], ONTEM)
    r = _avaliar(client, c["cli"], rid, 4, "  Quadra ótima!  ")
    assert r.status_code == 201
    lista = client.get(f"/espacos/{c['espaco']}/avaliacoes").get_json()
    assert (lista["media"], lista["total"]) == (4.0, 1)
    assert [(a["nota"], a["comentario"], a["autor"]) for a in lista["avaliacoes"]] == [(4, "Quadra ótima!", "João")]


def test_uma_avaliacao_por_reserva(client, c):
    rid = criar_reserva(c["cli_id"], c["espaco"], ONTEM)
    _avaliar(client, c["cli"], rid)
    assert _avaliar(client, c["cli"], rid).status_code == 409


def test_so_o_dono_da_reserva_avalia(client, c):
    rid = criar_reserva(c["cli_id"], c["espaco"], ONTEM)
    assert client.post(f"/reservas/{rid}/avaliacao", json={"nota": 5}).status_code == 401
    assert _avaliar(client, c["outro"], rid).status_code == 403
    assert _avaliar(client, c["loc"], rid).status_code == 403


def test_nao_avalia_antes_do_horario_nem_reserva_nao_realizada(client, c):
    futura = criar_reserva(c["cli_id"], c["espaco"], AMANHA)
    cancelada = criar_reserva(c["cli_id"], c["espaco"], ONTEM, status="Cancelada")
    faltou = criar_reserva(c["cli_id"], c["espaco"], ONTEM, status="Não compareceu")
    assert _avaliar(client, c["cli"], futura).status_code == 400
    assert _avaliar(client, c["cli"], cancelada).status_code == 400
    r = _avaliar(client, c["cli"], faltou)
    assert r.status_code == 400
    assert "compareceu" in r.get_json()["erro"]


@pytest.mark.parametrize("nota", [0, 6, "cinco", None, 4.5])
def test_nota_precisa_ser_inteira_de_1_a_5(client, c, nota):
    rid = criar_reserva(c["cli_id"], c["espaco"], ONTEM)
    assert _avaliar(client, c["cli"], rid, nota).status_code == 400


def test_falta_registrada_depois_remove_a_avaliacao(client, c):
    rid = criar_reserva(c["cli_id"], c["espaco"], ONTEM)
    _avaliar(client, c["cli"], rid, 1, "Péssimo")
    client.put(f"/reservas/{rid}/comparecimento", headers=c["loc"], json={"compareceu": False})
    assert client.get(f"/espacos/{c['espaco']}/avaliacoes").get_json()["total"] == 0


# --- onde a nota aparece ---

def test_media_aparece_no_catalogo_e_no_detalhe(client, c):
    _avaliar(client, c["cli"], criar_reserva(c["cli_id"], c["espaco"], ONTEM), 5)
    _avaliar(client, c["outro"], criar_reserva(c["outro_id"], c["espaco"], datetime(2026, 10, 3, 9)), 4)
    sem_nota = criar_espaco(1, nome="Nova")

    catalogo = {e["id"]: (e["nota_media"], e["total_avaliacoes"])
                for e in client.get("/espacos").get_json()["espacos"]}
    assert catalogo == {c["espaco"]: (4.5, 2), sem_nota: (None, 0)}
    detalhe = client.get(f"/espacos/{c['espaco']}").get_json()
    assert (detalhe["nota_media"], detalhe["total_avaliacoes"]) == (4.5, 2)


def test_filtro_de_avaliacao_minima(client, c):
    _avaliar(client, c["cli"], criar_reserva(c["cli_id"], c["espaco"], ONTEM), 3)
    criar_espaco(1, nome="Sem avaliações")
    ids = lambda qs: [e["id"] for e in client.get(f"/espacos?{qs}").get_json()["espacos"]]
    assert ids("nota_min=3") == [c["espaco"]]
    assert ids("nota_min=4") == []
    assert client.get("/espacos?nota_min=abc").status_code == 400


def test_minhas_reservas_dizem_o_que_pode_ser_avaliado(client, c):
    avaliada = criar_reserva(c["cli_id"], c["espaco"], ONTEM)
    pendente_de_nota = criar_reserva(c["cli_id"], c["espaco"], datetime(2026, 10, 3, 9))
    futura = criar_reserva(c["cli_id"], c["espaco"], AMANHA)
    _avaliar(client, c["cli"], avaliada, 5, "Top")

    minhas = {r["id"]: r for r in client.get("/reservas", headers=c["cli"]).get_json()["reservas"]}
    assert (minhas[avaliada]["pode_avaliar"], minhas[avaliada]["avaliacao"]) == (False, {"nota": 5, "comentario": "Top"})
    assert (minhas[pendente_de_nota]["pode_avaliar"], minhas[pendente_de_nota]["avaliacao"]) == (True, None)
    assert minhas[futura]["pode_avaliar"] is False


def test_locador_ve_a_avaliacao_na_reserva_recebida(client, c):
    rid = criar_reserva(c["cli_id"], c["espaco"], ONTEM)
    _avaliar(client, c["cli"], rid, 2, "Rede furada")
    recebidas = {r["id"]: r for r in client.get("/reservas/recebidas", headers=c["loc"]).get_json()["reservas"]}
    assert recebidas[rid]["avaliacao"] == {"nota": 2, "comentario": "Rede furada"}
