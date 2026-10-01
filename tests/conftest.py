"""Fixtures compartilhadas dos testes.

Os testes SEMPRE usam SQLite em memória: o `.env` local aponta para o banco real
(Supabase) e as fixtures fazem `drop_all()`, então a URL é sobrescrita antes de
qualquer import do app (o Config lê DATABASE_URL no import).
"""

import os

os.environ["DATABASE_URL"] = "sqlite://"

import pytest  # noqa: E402

from app import create_app, db  # noqa: E402
from app.factories.usuario_factory import UsuarioFactory  # noqa: E402
from app.models.espaco_esportivo_model import EspacoEsportivo  # noqa: E402
from app.models.reserva_model import Reserva  # noqa: E402
from app.services.validacao import parse_hora  # noqa: E402


@pytest.fixture
def app():
    app = create_app()
    app.config.update(TESTING=True)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def criar_usuario(tipo, email, senha="s", **kw):
    """Cria e persiste um usuário; devolve o id."""
    extras = {
        "locatario": {"cpf": kw.pop("cpf", email[:11].ljust(11, "0"))},
        "locador": {"cnpj": kw.pop("cnpj", email[:14].ljust(14, "0")), "razao_social": "Empresa"},
        "administrador": {},
    }[tipo]
    u = UsuarioFactory.criar_usuario(tipo, kw.pop("nome", tipo.title()), email, senha, **extras)
    db.session.add(u)
    db.session.commit()
    return u.id


def criar_espaco(locador_id, grade=None, **campos):
    """Cria um espaço; `grade` = [(dia_semana, "HH:MM", "HH:MM"), ...] define o horário."""
    dados = {"nome": "Quadra", "tipo_esporte": "Futsal", "preco_hora": 100.0,
             "locador_id": locador_id, "disponivel": True, "ativo": True}
    dados.update(campos)
    e = EspacoEsportivo(**dados)
    db.session.add(e)
    if grade:
        e.definir_horarios([(d, parse_hora(a), parse_hora(f)) for d, a, f in grade])
    db.session.commit()
    return e.id


def criar_reserva(locatario_id, espaco_id, inicio, fim=None, status="Confirmada"):
    r = Reserva(locatario_id=locatario_id, espaco_id=espaco_id, data_horario=inicio, data_fim=fim)
    r.status_texto = status
    db.session.add(r)
    db.session.commit()
    return r.id


def auth(client, email, senha="s"):
    """Faz login e devolve o header Authorization."""
    r = client.post("/usuarios/login", json={"email": email, "senha": senha})
    assert r.status_code == 200, r.get_json()
    return {"Authorization": f"Bearer {r.get_json()['token']}"}
