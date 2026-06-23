"""Orquestração da aplicação: fluxo login <-> shell autenticado e navegação por perfil.

Mantém a regra de acesso baseada no perfil do usuário (adm / locador / locatario).
A navegação usa uma **navbar horizontal** ("Arena Fácil"), no estilo da referência
visual do projeto.
"""

import flet as ft

from frontend.tema import aplicar_tema, COR_ESCURO, COR_PRIMARIA, COR_CARD, COR_TEXTO, COR_TEXTO_SUAVE
from frontend.sessao import (
    esta_logado, perfil_atual, obter_usuario, obter_token, limpar_sessao,
    PERFIL_ADM, PERFIL_LOCADOR, PERFIL_LOCATARIO,
)
from frontend.api_client import definir_token, limpar_token
from frontend.telas.login import tela_login
from frontend.telas.status import tela_status
from frontend.telas.perfil import tela_perfil
from frontend.telas.usuarios import tela_usuarios, tela_cadastro, tela_editar
from frontend.telas.locador import tela_meus_espacos, tela_reservas_recebidas
from frontend.telas.locatario import tela_buscar_espacos, tela_minhas_reservas


def _menu_por_perfil(perfil):
    """Retorna a lista de itens (icone, label, builder) do perfil (sem o Perfil)."""
    if perfil == PERFIL_ADM:
        return [
            (ft.Icons.DASHBOARD, "Dashboard", tela_status),
            (ft.Icons.PEOPLE, "Usuários", tela_usuarios),
            (ft.Icons.PERSON_ADD, "Cadastrar", tela_cadastro),
            (ft.Icons.EDIT, "Editar", tela_editar),
        ]
    if perfil == PERFIL_LOCADOR:
        return [
            (ft.Icons.DASHBOARD, "Dashboard", tela_status),
            (ft.Icons.STADIUM, "Meus Espaços", tela_meus_espacos),
            (ft.Icons.EVENT_NOTE, "Reservas", tela_reservas_recebidas),
        ]
    # PERFIL_LOCATARIO (padrão)
    return [
        (ft.Icons.SEARCH, "Buscar Quadras", tela_buscar_espacos),
        (ft.Icons.EVENT, "Minhas Reservas", tela_minhas_reservas),
        (ft.Icons.DASHBOARD, "Início", tela_status),
    ]


def main(page: ft.Page):
    page.title = "Arena Fácil"
    page.padding = 0
    if page.window:
        page.window.width = 1100
        page.window.height = 720
    aplicar_tema(page)

    def render():
        """(Re)constrói a interface conforme o estado de autenticação."""
        page.controls.clear()
        if not esta_logado(page):
            limpar_token()
            page.add(tela_login(page, on_sucesso=render))
            page.update()
            return
        # Garante que o api_client tenha o token (ex.: após recarregar a página).
        definir_token(obter_token(page))
        page.add(_shell_autenticado(page, on_logout=_logout))
        page.update()

    def _logout():
        limpar_sessao(page)
        limpar_token()
        render()

    def _shell_autenticado(page, on_logout):
        perfil = perfil_atual(page)
        usuario = obter_usuario(page)
        itens = _menu_por_perfil(perfil)
        area_conteudo = ft.Container(expand=True, padding=24)

        botoes_nav = []

        def navegar(index):
            area_conteudo.content = itens[index][2](page)
            for i, b in enumerate(botoes_nav):
                b.style = _estilo_nav(i == index)
            page.update()

        def _ir(index):
            return lambda e: navegar(index)

        for i, (icone, label, _) in enumerate(itens):
            botoes_nav.append(
                ft.TextButton(content=ft.Row(
                    [ft.Icon(icone, size=18), ft.Text(label, size=14, weight=ft.FontWeight.W_500)],
                    spacing=6, tight=True),
                    on_click=_ir(i), style=_estilo_nav(i == 0))
            )

        abrir_perfil = lambda e: _abrir_tela(area_conteudo, tela_perfil(page, on_logout=on_logout), botoes_nav, page)

        marca = ft.Row(
            [ft.Icon(ft.Icons.SPORTS_SOCCER, color=COR_PRIMARIA, size=26),
             ft.Text("Arena Fácil", size=18, weight=ft.FontWeight.BOLD, color=COR_PRIMARIA)],
            spacing=8, tight=True,
        )

        perfil_botao = ft.TextButton(
            content=ft.Row([ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=20),
                            ft.Text(usuario.get("nome") or "Perfil", size=14)], spacing=6, tight=True),
            on_click=abrir_perfil, style=_estilo_nav(False),
        )

        navbar = ft.Container(
            content=ft.Row(
                [marca, ft.Container(width=24), ft.Row(botoes_nav, spacing=4),
                 ft.Container(expand=True), perfil_botao],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=COR_CARD,
            padding=ft.Padding(20, 12, 20, 12),
            shadow=ft.BoxShadow(blur_radius=6, color="#11182714"),
        )

        navegar(0)

        return ft.Column([navbar, area_conteudo], expand=True, spacing=0)

    render()


def _estilo_nav(selecionado: bool) -> ft.ButtonStyle:
    return ft.ButtonStyle(
        color=COR_PRIMARIA if selecionado else COR_TEXTO,
        bgcolor=ft.Colors.with_opacity(0.10, COR_PRIMARIA) if selecionado else None,
        shape=ft.RoundedRectangleBorder(radius=10),
        padding=ft.Padding(14, 8, 14, 8),
    )


def _abrir_tela(area_conteudo, conteudo, botoes_nav, page):
    """Abre uma tela fora do menu (ex.: Perfil), limpando a seleção da navbar."""
    area_conteudo.content = conteudo
    for b in botoes_nav:
        b.style = _estilo_nav(False)
    page.update()
