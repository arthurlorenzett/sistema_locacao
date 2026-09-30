import pytest

from tests.conftest import criar_espaco, criar_usuario


@pytest.fixture
def precos(app):
    loc = criar_usuario("locador", "loc@t.com")
    return {p: criar_espaco(loc, nome=f"R$ {p}", preco_hora=p) for p in (50.0, 100.0, 200.0)}


def _precos(client, qs):
    return sorted(e["preco_hora"] for e in client.get(f"/espacos?{qs}").get_json()["espacos"])


def test_filtra_por_faixa_de_preco(client, precos):
    assert _precos(client, "preco_min=60&preco_max=150") == [100.0]
    assert _precos(client, "preco_min=100") == [100.0, 200.0]
    assert _precos(client, "preco_max=100") == [50.0, 100.0]


def test_faixa_de_preco_invertida_e_rejeitada(client, precos):
    r = client.get("/espacos?preco_min=200&preco_max=50")
    assert r.status_code == 400
    assert "mínimo maior que máximo" in r.get_json()["erro"]
