"""Gerenciamento da sessão do usuário autenticado (page.session).

Centraliza leitura/escrita dos dados de sessão para que as telas não dependam das
chaves cruas. O perfil é normalizado para um dos valores: 'adm', 'locador',
'locatario'.
"""

PERFIL_ADM = "adm"
PERFIL_LOCADOR = "locador"
PERFIL_LOCATARIO = "locatario"

# Mapeia o tipo_usuario persistido no banco para o perfil usado na navegação.
_MAPA_PERFIL = {
    "administrador": PERFIL_ADM,
    "adm": PERFIL_ADM,
    "locador": PERFIL_LOCADOR,
    "locatario": PERFIL_LOCATARIO,
}


def salvar_usuario(page, dados):
    """Persiste na sessão os dados retornados pelo endpoint de login."""
    page.session.set("usuario_id", dados.get("id"))
    page.session.set("nome", dados.get("nome"))
    page.session.set("email", dados.get("email"))
    page.session.set("tipo_usuario", dados.get("tipo_usuario"))


def obter_usuario(page):
    """Retorna um dict com os dados do usuário logado (ou vazios)."""
    return {
        "usuario_id": page.session.get("usuario_id"),
        "nome": page.session.get("nome"),
        "email": page.session.get("email"),
        "tipo_usuario": page.session.get("tipo_usuario"),
    }


def esta_logado(page):
    return page.session.get("usuario_id") is not None


def perfil_atual(page):
    """Perfil normalizado do usuário logado (ou None)."""
    tipo = page.session.get("tipo_usuario")
    if tipo is None:
        return None
    return _MAPA_PERFIL.get(str(tipo).lower(), PERFIL_LOCATARIO)


def limpar_sessao(page):
    page.session.clear()
