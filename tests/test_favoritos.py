import pytest

from app import db
from app.models.espaco_esportivo_model import EspacoEsportivo
from tests.conftest import auth, criar_espaco, criar_usuario


@pytest.fixture
def cenario(app):
    loc = criar_usuario("locador", "loc@t.com")
    criar_usuario("locatario", "cli@t.com", cpf="11111111111")
    return {"e1": criar_espaco(loc, nome="Quadra 1"), "e2": criar_espaco(loc, nome="Quadra 2")}


def _ids(resp):
    return [e["id"] for e in resp.get_json()["espacos"]]


def test_locatario_favorita_e_lista(client, cenario):
    cli = auth(client, "cli@t.com")
    assert client.post(f"/favoritos/{cenario['e1']}", headers=cli).status_code == 201
    r = client.get("/favoritos", headers=cli)
    assert r.status_code == 200
    assert _ids(r) == [cenario["e1"]]


def test_favoritar_duas_vezes_nao_duplica(client, cenario):
    cli = auth(client, "cli@t.com")
    client.post(f"/favoritos/{cenario['e1']}", headers=cli)
    assert client.post(f"/favoritos/{cenario['e1']}", headers=cli).status_code == 200
    assert _ids(client.get("/favoritos", headers=cli)) == [cenario["e1"]]


def test_remove_favorito(client, cenario):
    cli = auth(client, "cli@t.com")
    client.post(f"/favoritos/{cenario['e1']}", headers=cli)
    assert client.delete(f"/favoritos/{cenario['e1']}", headers=cli).status_code == 200
    assert _ids(client.get("/favoritos", headers=cli)) == []


def test_favoritos_exige_locatario(client, cenario):
    assert client.get("/favoritos").status_code == 401
    assert client.get("/favoritos", headers=auth(client, "loc@t.com")).status_code == 403


def test_favoritar_espaco_inexistente(client, cenario):
    assert client.post("/favoritos/999", headers=auth(client, "cli@t.com")).status_code == 404


def test_favoritos_nao_mostra_espaco_desativado(client, cenario):
    cli = auth(client, "cli@t.com")
    client.post(f"/favoritos/{cenario['e1']}", headers=cli)
    db.session.get(EspacoEsportivo, cenario["e1"]).ativo = False
    db.session.commit()
    assert _ids(client.get("/favoritos", headers=cli)) == []


def test_catalogo_marca_favoritos_do_locatario_logado(client, cenario):
    cli = auth(client, "cli@t.com")
    client.post(f"/favoritos/{cenario['e1']}", headers=cli)

    marcados = {e["id"]: e["favorito"] for e in client.get("/espacos", headers=cli).get_json()["espacos"]}
    assert marcados == {cenario["e1"]: True, cenario["e2"]: False}

    anonimo = client.get("/espacos").get_json()["espacos"]
    assert all(e["favorito"] is False for e in anonimo)
