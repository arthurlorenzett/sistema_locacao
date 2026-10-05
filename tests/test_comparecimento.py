from datetime import datetime

import pytest

from app.services import validacao
from tests.conftest import auth, criar_espaco, criar_reserva, criar_usuario

ONTEM_9H, ONTEM_10H = datetime(2026, 10, 4, 9), datetime(2026, 10, 4, 10)
AMANHA_9H = datetime(2026, 10, 6, 9)


@pytest.fixture
def c(app, client, monkeypatch):
    # "Agora" congelado numa segunda-feira, 10:30 (horário de Brasília).
    monkeypatch.setattr(validacao, "agora", lambda: datetime(2026, 10, 5, 10, 30))
    loc = criar_usuario("locador", "loc@t.com")
    criar_usuario("locador", "outro@t.com", cnpj="99999999999999")
    cli = criar_usuario("locatario", "cli@t.com", cpf="11111111111", nome="João Silva")
    espaco = criar_espaco(loc)
    return {"espaco": espaco, "cli_id": cli, "loc": auth(client, "loc@t.com"),
            "cli": auth(client, "cli@t.com"), "outro": auth(client, "outro@t.com")}


def _registrar(client, headers, reserva_id, compareceu):
    return client.put(f"/reservas/{reserva_id}/comparecimento", headers=headers, json={"compareceu": compareceu})


def _recebidas(client, c):
    return {r["id"]: r for r in client.get("/reservas/recebidas", headers=c["loc"]).get_json()["reservas"]}


def test_locador_registra_que_o_cliente_compareceu(client, c):
    rid = criar_reserva(c["cli_id"], c["espaco"], ONTEM_9H, ONTEM_10H)
    r = _registrar(client, c["loc"], rid, True)
    assert r.status_code == 200
    assert r.get_json()["status"] == "Concluída"


def test_locador_registra_falta(client, c):
    rid = criar_reserva(c["cli_id"], c["espaco"], ONTEM_9H, ONTEM_10H)
    assert _registrar(client, c["loc"], rid, False).get_json()["status"] == "Não compareceu"


def test_so_depois_do_horario_da_reserva(client, c):
    rid = criar_reserva(c["cli_id"], c["espaco"], AMANHA_9H)
    r = _registrar(client, c["loc"], rid, True)
    assert r.status_code == 400
    assert "depois do horário" in r.get_json()["erro"]


def test_so_reserva_confirmada_e_uma_vez_so(client, c):
    pendente = criar_reserva(c["cli_id"], c["espaco"], ONTEM_9H, status="Pendente")
    assert _registrar(client, c["loc"], pendente, True).status_code == 400
    rid = criar_reserva(c["cli_id"], c["espaco"], ONTEM_10H)
    _registrar(client, c["loc"], rid, True)
    assert _registrar(client, c["loc"], rid, False).status_code == 400


def test_so_o_dono_do_espaco_registra(client, c):
    rid = criar_reserva(c["cli_id"], c["espaco"], ONTEM_9H)
    assert client.put(f"/reservas/{rid}/comparecimento", json={"compareceu": True}).status_code == 401
    assert _registrar(client, c["cli"], rid, True).status_code == 403
    assert _registrar(client, c["outro"], rid, True).status_code == 403


def test_reserva_realizada_nao_pode_ser_cancelada(client, c):
    rid = criar_reserva(c["cli_id"], c["espaco"], ONTEM_9H)
    _registrar(client, c["loc"], rid, True)
    assert client.put(f"/reservas/{rid}/cancelar", headers=c["cli"]).status_code == 400


def test_reservas_recebidas_mostram_cliente_e_indice_de_confianca(client, c):
    r1 = criar_reserva(c["cli_id"], c["espaco"], datetime(2026, 10, 1, 9))
    r2 = criar_reserva(c["cli_id"], c["espaco"], datetime(2026, 10, 2, 9))
    criar_reserva(c["cli_id"], c["espaco"], datetime(2026, 10, 3, 9))                      # passou, sem registro
    criar_reserva(c["cli_id"], c["espaco"], datetime(2026, 9, 30, 9), status="Cancelada")  # não conta
    futura = criar_reserva(c["cli_id"], c["espaco"], AMANHA_9H)                              # ainda não conta
    _registrar(client, c["loc"], r1, True)
    _registrar(client, c["loc"], r2, False)

    item = _recebidas(client, c)[futura]
    assert item["locatario_nome"] == "João Silva"
    # comparecimentos: r1 (registrado) + 3/10 (presumido); faltas: r2
    assert item["confianca"] == {"comparecimentos": 2, "faltas": 1, "percentual": 67}


def test_cliente_sem_historico_nao_tem_percentual(client, c):
    novo = criar_usuario("locatario", "novo@t.com", cpf="22222222222")
    rid = criar_reserva(novo, c["espaco"], AMANHA_9H, status="Pendente")
    assert _recebidas(client, c)[rid]["confianca"] == {"comparecimentos": 0, "faltas": 0, "percentual": None}


def test_reservas_indicam_as_acoes_possiveis(client, c):
    passada = criar_reserva(c["cli_id"], c["espaco"], ONTEM_9H)
    futura = criar_reserva(c["cli_id"], c["espaco"], AMANHA_9H)
    recebidas = _recebidas(client, c)
    assert (recebidas[passada]["pode_registrar_comparecimento"], recebidas[passada]["pode_cancelar"]) == (True, False)
    assert (recebidas[futura]["pode_registrar_comparecimento"], recebidas[futura]["pode_cancelar"]) == (False, True)
    minhas = {r["id"]: r for r in client.get("/reservas", headers=c["cli"]).get_json()["reservas"]}
    assert (minhas[passada]["pode_cancelar"], minhas[futura]["pode_cancelar"]) == (False, True)
