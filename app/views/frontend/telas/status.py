"""Dashboard / Status da API (visível para o administrador)."""

from datetime import datetime

import flet as ft

from frontend.api_client import api_get
from frontend.componentes import cabecalho_tela
from frontend.tema import COR_PRIMARIA, COR_TEXTO, COR_TEXTO_SUAVE, COR_ERRO, COR_SUCESSO


def tela_status(page: ft.Page):
    conteudo = ft.Column(spacing=8)

    def verificar(e=None):
        conteudo.controls.clear()
        dados, code = api_get("/")
        if code == 0:
            conteudo.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.CLOUD_OFF, color=COR_ERRO, size=32),
                        ft.Column([
                            ft.Text("Backend offline", weight=ft.FontWeight.BOLD, color=COR_ERRO),
                            ft.Text(dados.get("erro", ""), size=12, color=COR_TEXTO_SUAVE),
                        ], spacing=2),
                    ]),
                    padding=16, bgcolor="#FEE2E2", border_radius=12,
                )
            )
        else:
            conteudo.controls += [
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.CLOUD_DONE, color=COR_SUCESSO, size=32),
                        ft.Column([
                            ft.Text("API online e operacional", weight=ft.FontWeight.BOLD, color=COR_SUCESSO),
                            ft.Text(dados.get("mensagem", ""), size=12, color=COR_TEXTO_SUAVE),
                        ], spacing=2),
                    ]),
                    padding=16, bgcolor="#D1FAE5", border_radius=12,
                ),
                ft.Container(height=8),
                ft.Text("Informações do sistema:", weight=ft.FontWeight.BOLD, color=COR_TEXTO),
                ft.Text(f"Projeto:  {dados.get('projeto', '-')}", size=13),
                ft.Text(f"Versão:   {dados.get('versao', '-')}", size=13),
                ft.Text(f"Verificado em: {datetime.now().strftime('%H:%M:%S')}",
                        size=12, color=COR_TEXTO_SUAVE),
            ]
        page.update()

    verificar()

    return ft.Column(
        [
            cabecalho_tela(
                "Dashboard",
                acoes=[ft.IconButton(ft.Icons.REFRESH, tooltip="Verificar novamente",
                                     on_click=verificar, icon_color=COR_PRIMARIA)],
            ),
            ft.Container(conteudo, padding=ft.Padding(0, 16, 0, 0)),
        ],
        spacing=8,
    )
