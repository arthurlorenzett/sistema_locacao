"""Telas do perfil Locatário (placeholders preparados para integração futura)."""

import flet as ft

from frontend.componentes import cabecalho_tela, card_placeholder

# from frontend.api_client import api_get, api_post
# def buscar_espacos(filtros=None):
#     return api_get("/espacos")  # rota futura
# def realizar_reserva(locatario_id, espaco_id, data_horario):
#     return api_post("/reservas/realizar", {...})  # endpoint já existe no backend


def tela_buscar_espacos(page: ft.Page):
    return ft.Column(
        [
            cabecalho_tela("Buscar Espaços"),
            ft.Container(
                content=ft.ResponsiveRow(
                    [
                        card_placeholder(ft.Icons.SPORTS_SOCCER, "Futebol",
                                         "Encontre quadras de society e campos."),
                        card_placeholder(ft.Icons.SPORTS_BASKETBALL, "Basquete",
                                         "Quadras poliesportivas disponíveis."),
                        card_placeholder(ft.Icons.SPORTS_TENNIS, "Tênis",
                                         "Reserve quadras por hora."),
                    ],
                    run_spacing=16, spacing=16,
                ),
                padding=ft.Padding(0, 16, 0, 0),
            ),
        ],
        spacing=8, scroll=ft.ScrollMode.AUTO,
    )


def tela_minhas_reservas(page: ft.Page):
    return ft.Column(
        [
            cabecalho_tela("Minhas Reservas"),
            ft.Container(
                content=ft.ResponsiveRow(
                    [
                        card_placeholder(ft.Icons.HOURGLASS_TOP, "Pendentes",
                                         "Reservas aguardando confirmação do locador."),
                        card_placeholder(ft.Icons.CHECK_CIRCLE, "Confirmadas",
                                         "Seus próximos agendamentos."),
                        card_placeholder(ft.Icons.HISTORY, "Histórico",
                                         "Reservas anteriores e canceladas."),
                    ],
                    run_spacing=16, spacing=16,
                ),
                padding=ft.Padding(0, 16, 0, 0),
            ),
        ],
        spacing=8, scroll=ft.ScrollMode.AUTO,
    )
