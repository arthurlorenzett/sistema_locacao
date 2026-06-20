"""Tela de login — ponto de entrada obrigatório da aplicação."""

import flet as ft

from frontend.api_client import api_login
from frontend.sessao import salvar_usuario
from frontend.componentes import campo, botao_primario, snack, card
from frontend.tema import (
    COR_AZUL_ESCURO, COR_FUNDO, COR_TEXTO, COR_TEXTO_SUAVE, COR_ERRO, COR_AVISO,
)


def tela_login(page: ft.Page, on_sucesso):
    """Renderiza o formulário de login.

    `on_sucesso` é chamado (sem argumentos) após autenticação bem-sucedida para
    que o app reconstrua a interface autenticada.
    """
    f_email = campo("E-mail", hint="seu@email.com", width=320)
    f_senha = campo("Senha", password=True, width=320)

    def entrar(e):
        email = (f_email.value or "").strip()
        senha = f_senha.value or ""
        if not email or not senha:
            snack(page, "Preencha e-mail e senha.", COR_AVISO)
            return

        dados, code = api_login(email, senha)
        if code == 200:
            salvar_usuario(page, dados)
            on_sucesso()
        elif code == 0:
            snack(page, dados.get("erro", "Sem conexão com o servidor."), COR_ERRO)
        else:
            snack(page, dados.get("erro", "Não foi possível entrar."), COR_ERRO)

    f_senha.on_submit = entrar

    formulario = card(
        ft.Column(
            [
                ft.Icon(ft.Icons.SPORTS_SOCCER, color=COR_AZUL_ESCURO, size=48),
                ft.Text("Espaços Esportivos", size=22, weight=ft.FontWeight.BOLD, color=COR_TEXTO),
                ft.Text("Acesse sua conta", size=13, color=COR_TEXTO_SUAVE),
                ft.Container(height=8),
                f_email,
                f_senha,
                ft.Container(height=8),
                botao_primario("Entrar", entrar, width=320, icone=ft.Icons.LOGIN),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
            tight=True,
        ),
        padding=32,
    )

    return ft.Container(
        content=ft.Column(
            [formulario],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        expand=True,
        bgcolor=COR_FUNDO,
        alignment=ft.alignment.Alignment(0, 0),
        padding=24,
    )
