from datetime import datetime

import pytest

from app.services import validacao
from tests.conftest import auth, criar_espaco, criar_reserva, criar_usuario

# "Agora" é segunda 05/10/2026 10:30; as terças seguintes: 06, 13, 20 e 27/10.
TERCAS = ["2026-10-06", "2026-10-13", "2026-10-20", "2026-10-27"]


@pytest.fixture
def c(app, client, monkeypatch):
    monkeypatch.setattr(validacao, "agora", lambda: datetime(2026, 10, 5, 10, 30))
    loc = criar_usuario("locador", "loc@t.com")
    cli = criar_usuario("locatario", "cli@t.com", cpf="11111111111")
    outro = criar_usuario("locatario", "outro@t.com", cpf="22222222222")
    espaco = criar_espaco(loc, preco_hora=100.0)
    return {"espaco": espaco, "cli_id": cli, "outro_id": outro, "loc": auth(client, "loc@t.com"),
            "cli": auth(client, "cli@t.com"), "outro": auth(client, "outro@t.com")}


def _serie(client, c, semanas=4, **extra):
    return client.post("/reservas/recorrente", headers=c["cli"], json=dict({
        "espaco_id": c["espaco"], "data_horario": "2026-10-06T20:00", "data_fim": "2026-10-06T21:00",
        "semanas": semanas, "metodo_pagamento": "online"}, **extra))


def _minhas(client, c):
    return sorted(client.get("/reservas", headers=c["cli"]).get_json()["reservas"], key=lambda r: r["data_horario"])


def test_cria_uma_reserva_por_semana_ja_confirmadas_e_ligadas_pela_serie(client, c):
    r = _serie(client, c)
    assert r.status_code == 201
    corpo = r.get_json()
    assert (corpo["reservas"], corpo["recusadas"], corpo["valor_total"]) == (4, [], 400.0)

    minhas = _minhas(client, c)
    assert [m["data_horario"] for m in minhas] == [f"{d}T20:00:00" for d in TERCAS]
    assert {m["status"] for m in minhas} == {"Confirmada"}
    assert {m["serie_id"] for m in minhas} == {corpo["serie_id"]}


def test_data_ocupada_fica_de_fora_e_as_outras_sao_reservadas(client, c):
    criar_reserva(c["outro_id"], c["espaco"], datetime(2026, 10, 13, 20), datetime(2026, 10, 13, 21))
    corpo = _serie(client, c).get_json()
    assert corpo["reservas"] == 3
    assert [x["inicio"] for x in corpo["recusadas"]] == ["2026-10-13T20:00:00"]
    assert "confirmada" in corpo["recusadas"][0]["motivo"]
    assert [m["data_horario"][:10] for m in _minhas(client, c)] == [TERCAS[0], TERCAS[2], TERCAS[3]]


def test_data_bloqueada_pelo_locador_fica_de_fora(client, c):
    client.post(f"/espacos/{c['espaco']}/bloqueios", headers=c["loc"], json={"data": "2026-10-20", "dia_inteiro": True})
    corpo = _serie(client, c).get_json()
    assert corpo["reservas"] == 3
    assert "bloqueado" in corpo["recusadas"][0]["motivo"]


def test_se_nenhuma_data_estiver_livre_nada_e_reservado(client, c):
    for dia in (6, 13):
        criar_reserva(c["outro_id"], c["espaco"], datetime(2026, 10, dia, 20), datetime(2026, 10, dia, 21))
    r = _serie(client, c, semanas=2)
    assert r.status_code == 400
    assert len(r.get_json()["recusadas"]) == 2
    assert _minhas(client, c) == []


@pytest.mark.parametrize("semanas", [1, 13, "quatro", None])
def test_quantidade_de_semanas_invalida(client, c, semanas):
    assert _serie(client, c, semanas=semanas).status_code == 400


def test_forma_de_pagamento_invalida_nao_cria_nada(client, c):
    assert _serie(client, c, metodo_pagamento="fiado").status_code == 400
    assert _minhas(client, c) == []


def test_previa_mostra_cada_data_com_disponibilidade_e_preco(client, c):
    criar_reserva(c["outro_id"], c["espaco"], datetime(2026, 10, 13, 20), datetime(2026, 10, 13, 21))
    r = client.get(f"/reservas/recorrente/previa?espaco_id={c['espaco']}"
                   "&data_horario=2026-10-06T20:00&data_fim=2026-10-06T21:00&semanas=4", headers=c["cli"])
    assert r.status_code == 200
    corpo = r.get_json()
    assert [(d["inicio"][:10], d["disponivel"]) for d in corpo["datas"]] == [
        (TERCAS[0], True), (TERCAS[1], False), (TERCAS[2], True), (TERCAS[3], True)]
    assert (corpo["disponiveis"], corpo["valor_total"]) == (3, 300.0)
    assert _minhas(client, c) == []  # a prévia não reserva nada


def test_cancelar_a_serie_cancela_so_as_datas_que_ainda_nao_passaram(client, c, monkeypatch):
    serie = _serie(client, c).get_json()["serie_id"]
    # Passa uma semana: a primeira terça já aconteceu.
    monkeypatch.setattr(validacao, "agora", lambda: datetime(2026, 10, 8, 10, 0))
    assert client.put(f"/reservas/serie/{serie}/cancelar", headers=c["outro"]).status_code == 403
    r = client.put(f"/reservas/serie/{serie}/cancelar", headers=c["cli"])
    assert r.status_code == 200
    assert r.get_json()["canceladas"] == 3
    assert [m["status"] for m in _minhas(client, c)] == ["Confirmada", "Cancelada", "Cancelada", "Cancelada"]


def test_serie_inexistente(client, c):
    assert client.put("/reservas/serie/nao-existe/cancelar", headers=c["cli"]).status_code == 404
