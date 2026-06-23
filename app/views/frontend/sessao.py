"""Gerenciamento da sessão do usuário autenticado."""

PERFIL_ADM = "adm"
PERFIL_LOCADOR = "locador"
PERFIL_LOCATARIO = "locatario"

_MAPA_PERFIL = {
    "administrador": PERFIL_ADM,
    "adm": PERFIL_ADM,
    "locador": PERFIL_LOCADOR,
    "locatario": PERFIL_LOCATARIO,
}


def salvar_usuario(page, dados):
    page.session.store.set("usuario_id", dados.get("id"))
    page.session.store.set("nome", dados.get("nome"))
    page.session.store.set("email", dados.get("email"))
    page.session.store.set("tipo_usuario", dados.get("tipo_usuario"))
    if dados.get("token"):
        page.session.store.set("token", dados.get("token"))


def obter_usuario(page):
    return {
        "usuario_id": page.session.store.get("usuario_id"),
        "nome": page.session.store.get("nome"),
        "email": page.session.store.get("email"),
        "tipo_usuario": page.session.store.get("tipo_usuario"),
    }


def obter_token(page):
    return page.session.store.get("token")


def esta_logado(page):
    return page.session.store.get("usuario_id") is not None


def perfil_atual(page):
    tipo = page.session.store.get("tipo_usuario")

    if tipo is None:
        return None

    return _MAPA_PERFIL.get(
        str(tipo).lower(),
        PERFIL_LOCATARIO
    )


def limpar_sessao(page):
    for key in page.session.store.get_keys():
        page.session.store.remove(key)