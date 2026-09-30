import os

import pytest

# O Config exige DATABASE_URL; os testes usam um SQLite em memória.
os.environ.setdefault("DATABASE_URL", "sqlite://")

from app import create_app, db
from app.factories.usuario_factory import UsuarioFactory


@pytest.fixture
def client():
    app = create_app()
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI="sqlite://")
    with app.app_context():
        db.create_all()
        db.session.add(UsuarioFactory.criar_usuario("administrador", "Admin", "admin@t.com", "s1"))
        db.session.add(UsuarioFactory.criar_usuario("locatario", "Cli", "cli@t.com", "s2", cpf="12345678901"))
        db.session.commit()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def _token(client, email, senha):
    r = client.post("/usuarios/login", json={"email": email, "senha": senha})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.get_json()['token']}"}


def test_listar_usuarios_exige_admin(client):
    assert client.get("/usuarios").status_code == 401
    assert client.get("/usuarios", headers=_token(client, "cli@t.com", "s2")).status_code == 403
    r = client.get("/usuarios", headers=_token(client, "admin@t.com", "s1"))
    assert r.status_code == 200
    assert r.get_json()["total_usuarios"] == 2


def test_usuario_so_acessa_o_proprio_cadastro(client):
    cli = _token(client, "cli@t.com", "s2")
    assert client.get("/usuarios/2", headers=cli).status_code == 200
    assert client.get("/usuarios/1", headers=cli).status_code == 403
    assert client.put("/usuarios/1", json={"nome": "x"}, headers=cli).status_code == 403


def test_deletar_exige_admin(client):
    assert client.delete("/usuarios/2", headers=_token(client, "cli@t.com", "s2")).status_code == 403
    assert client.delete("/usuarios/2", headers=_token(client, "admin@t.com", "s1")).status_code == 200


def test_cadastro_publico_nao_cria_admin(client):
    novo_adm = {"tipo": "administrador", "nome": "X", "email": "x@t.com", "senha": "1"}
    assert client.post("/usuarios", json=novo_adm).status_code == 401
    assert client.post("/usuarios", json=novo_adm,
                       headers=_token(client, "cli@t.com", "s2")).status_code == 403
    assert client.post("/usuarios", json=novo_adm,
                       headers=_token(client, "admin@t.com", "s1")).status_code == 201

    locatario = {"tipo": "locatario", "nome": "Y", "email": "y@t.com", "senha": "1", "cpf": "98765432100"}
    assert client.post("/usuarios", json=locatario).status_code == 201


def test_cadastro_email_duplicado_retorna_409(client):
    dup = {"tipo": "locatario", "nome": "Z", "email": "cli@t.com", "senha": "1", "cpf": "11122233344"}
    assert client.post("/usuarios", json=dup).status_code == 409
