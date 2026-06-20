"""Tela de perfil do usuário logado, com ação de logout."""

import flet as ft

from frontend.sessao import obter_usuario
from frontend.componentes import cabecalho_tela, botao_perigo, card
from frontend.tema import COR_PRIMARIA, COR_TEXTO, COR_TEXTO_SUAVE


def tela_perfil(page: ft.Page, on_logout):
    """`on_logout` é chamado (sem argumentos) ao clicar em Sair."""
    usuario = obter_usuario(page)

    def linha(rotulo, valor):
        return ft.Row(
            [
                ft.Text(rotulo, size=13, color=COR_TEXTO_SUAVE, width=80),
                ft.Text(str(valor or "-"), size=14, color=COR_TEXTO, weight=ft.FontWeight.W_500),
            ],
            spacing=8,
        )

    detalhes = card(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.ACCOUNT_CIRCLE, color=COR_PRIMARIA, size=56),
                        ft.Column(
                            [
                                ft.Text(usuario["nome"] or "Usuário", size=18,
                                        weight=ft.FontWeight.BOLD, color=COR_TEXTO),
                                ft.Text((usuario["tipo_usuario"] or "").capitalize(),
                                        size=13, color=COR_TEXTO_SUAVE),
                            ],
                            spacing=2,
                        ),
                    ],
                    spacing=16,
                ),
                ft.Divider(height=16, color="transparent"),
                linha("ID", usuario["usuario_id"]),
                linha("Nome", usuario["nome"]),
                linha("E-mail", usuario["email"]),
                linha("Perfil", (usuario["tipo_usuario"] or "").capitalize()),
                ft.Divider(height=20, color="transparent"),
                botao_perigo("Sair", lambda e: on_logout(), width=160, icone=ft.Icons.LOGOUT),
            ],
            spacing=10,
        ),
        padding=28,
    )

    return ft.Column(
        [
            cabecalho_tela("Meu Perfil"),
            ft.Container(detalhes, padding=ft.Padding(0, 16, 0, 0), width=480),
        ],
        spacing=8,
    )
