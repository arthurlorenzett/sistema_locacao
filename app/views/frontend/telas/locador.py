"""Telas do perfil Locador (placeholders preparados para integração futura).

As funções de comunicação com a API ficam delineadas, mas ainda não implementadas,
para que a integração com o backend seja adicionada sem reestruturar a tela.
"""

import flet as ft

from frontend.componentes import cabecalho_tela, card_placeholder

# from frontend.api_client import api_get
# def carregar_meus_espacos(locador_id):
#     return api_get(f"/espacos?locador_id={locador_id}")  # rota futura
# def carregar_reservas_recebidas(locador_id):
#     return api_get(f"/reservas/recebidas?locador_id={locador_id}")  # rota futura


def tela_meus_espacos(page: ft.Page):
    return ft.Column(
        [
            cabecalho_tela("Meus Espaços"),
            ft.Container(
                content=ft.ResponsiveRow(
                    [
                        card_placeholder(ft.Icons.STADIUM, "Quadra Society",
                                         "Cadastre e gerencie seus espaços esportivos."),
                        card_placeholder(ft.Icons.SPORTS_TENNIS, "Quadra de Tênis",
                                         "Defina disponibilidade e preço por hora."),
                        card_placeholder(ft.Icons.ADD_BUSINESS, "Novo espaço",
                                         "Em breve: cadastro de novos espaços."),
                    ],
                    run_spacing=16, spacing=16,
                ),
                padding=ft.Padding(0, 16, 0, 0),
            ),
        ],
        spacing=8, scroll=ft.ScrollMode.AUTO,
    )


def tela_reservas_recebidas(page: ft.Page):
    return ft.Column(
        [
            cabecalho_tela("Reservas Recebidas"),
            ft.Container(
                content=ft.ResponsiveRow(
                    [
                        card_placeholder(ft.Icons.PENDING_ACTIONS, "Pendentes",
                                         "Solicitações aguardando sua confirmação."),
                        card_placeholder(ft.Icons.EVENT_AVAILABLE, "Confirmadas",
                                         "Reservas confirmadas dos seus espaços."),
                        card_placeholder(ft.Icons.EVENT_BUSY, "Canceladas",
                                         "Histórico de reservas canceladas."),
                    ],
                    run_spacing=16, spacing=16,
                ),
                padding=ft.Padding(0, 16, 0, 0),
            ),
        ],
        spacing=8, scroll=ft.ScrollMode.AUTO,
    )
