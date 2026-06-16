"""Orquestração da aplicação: fluxo login <-> shell autenticado e navegação por perfil.

Mantém a regra de acesso baseada no perfil do usuário (adm / locador / locatario),
montando dinamicamente os menus e telas correspondentes.
"""

import flet as ft

from frontend.tema import aplicar_tema, COR_AZUL_ESCURO, COR_AZUL_MEDIO, COR_BORDA
from frontend.sessao import (
    esta_logado, perfil_atual, limpar_sessao,
    PERFIL_ADM, PERFIL_LOCADOR, PERFIL_LOCATARIO,
)
from frontend.telas.login import tela_login
from frontend.telas.status import tela_status
from frontend.telas.perfil import tela_perfil
from frontend.telas.usuarios import tela_usuarios, tela_cadastro, tela_editar
from frontend.telas.locador import tela_meus_espacos, tela_reservas_recebidas
from frontend.telas.locatario import tela_buscar_espacos, tela_minhas_reservas


def _menu_por_perfil(perfil, abrir_perfil):
    """Retorna a lista de itens de menu (icone, icone_sel, label, builder) do perfil.

    `builder` recebe a página e devolve o conteúdo da tela. `abrir_perfil` é o
    builder da tela de perfil (já com o logout vinculado).
    """
    item_perfil = (ft.Icons.ACCOUNT_CIRCLE_OUTLINED, ft.Icons.ACCOUNT_CIRCLE, "Perfil", abrir_perfil)

    if perfil == PERFIL_ADM:
        return [
            (ft.Icons.DASHBOARD_OUTLINED, ft.Icons.DASHBOARD, "Dashboard", tela_status),
            (ft.Icons.PEOPLE_OUTLINED, ft.Icons.PEOPLE, "Usuários", tela_usuarios),
            (ft.Icons.PERSON_ADD_OUTLINED, ft.Icons.PERSON_ADD, "Cadastrar", tela_cadastro),
            (ft.Icons.EDIT_OUTLINED, ft.Icons.EDIT, "Editar", tela_editar),
            item_perfil,
        ]
    if perfil == PERFIL_LOCADOR:
        return [
            (ft.Icons.DASHBOARD_OUTLINED, ft.Icons.DASHBOARD, "Dashboard", tela_status),
            (ft.Icons.STADIUM_OUTLINED, ft.Icons.STADIUM, "Meus Espaços", tela_meus_espacos),
            (ft.Icons.EVENT_NOTE_OUTLINED, ft.Icons.EVENT_NOTE, "Reservas", tela_reservas_recebidas),
            item_perfil,
        ]
    # PERFIL_LOCATARIO (padrão)
    return [
        (ft.Icons.DASHBOARD_OUTLINED, ft.Icons.DASHBOARD, "Dashboard", tela_status),
        (ft.Icons.SEARCH_OUTLINED, ft.Icons.SEARCH, "Buscar", tela_buscar_espacos),
        (ft.Icons.EVENT_OUTLINED, ft.Icons.EVENT, "Reservas", tela_minhas_reservas),
        item_perfil,
    ]


def main(page: ft.Page):
    page.title = "Espaços Esportivos"
    page.padding = 0
    if page.window:
        page.window.width = 1000
        page.window.height = 680
    aplicar_tema(page)

    def render():
        """(Re)constrói a interface conforme o estado de autenticação."""
        page.controls.clear()
        if not esta_logado(page):
            page.add(tela_login(page, on_sucesso=render))
            return
        page.add(_shell_autenticado(page, on_logout=_logout))
        page.update()

    def _logout():
        limpar_sessao(page)
        render()

    def _shell_autenticado(page, on_logout):
        perfil = perfil_atual(page)
        area_conteudo = ft.Container(expand=True, padding=24)

        abrir_perfil = lambda pg: tela_perfil(pg, on_logout=on_logout)
        itens = _menu_por_perfil(perfil, abrir_perfil)

        def navegar(index):
            area_conteudo.content = itens[index][3](page)
            page.update()

        rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            bgcolor=COR_AZUL_ESCURO,
            indicator_color=COR_AZUL_MEDIO,
            min_width=92,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ic, selected_icon=ic_sel, label=label,
                    padding=ft.Padding(0, 4, 0, 4),
                )
                for ic, ic_sel, label, _ in itens
            ],
            on_change=lambda e: navegar(e.control.selected_index),
            leading=ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.SPORTS_SOCCER, color="white", size=32),
                        ft.Text("Espaços\nEsportivos", color="white", size=11,
                                text_align=ft.TextAlign.CENTER),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4,
                ),
                padding=ft.Padding(0, 16, 0, 16),
            ),
        )

        navegar(0)

        return ft.Row(
            [
                ft.Container(content=rail, bgcolor=COR_AZUL_ESCURO),
                ft.VerticalDivider(width=1, color=COR_BORDA),
                area_conteudo,
            ],
            expand=True,
            spacing=0,
        )

    render()
