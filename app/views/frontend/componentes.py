"""Componentes visuais reutilizáveis.

Centraliza a criação de campos, botões, cards e feedback (SnackBar) para manter
padronização visual e evitar duplicação entre as telas.
"""

import flet as ft

from frontend.tema import (
    COR_PRIMARIA, COR_CARD, COR_TEXTO, COR_TEXTO_SUAVE,
    COR_BORDA, COR_ERRO, COR_SUCESSO,
)


def snack(page, msg, cor=COR_SUCESSO):
    """Exibe uma mensagem temporária sem travar a aplicação."""
    page.snack_bar = ft.SnackBar(
        content=ft.Text(msg, color="white"),
        bgcolor=cor,
        duration=3000,
    )
    page.snack_bar.open = True
    page.update()


def titulo_secao(texto):
    return ft.Text(texto, size=24, weight=ft.FontWeight.BOLD, color=COR_TEXTO)


def campo(label, hint="", password=False, width=320, value=""):
    """TextField padronizado com texto escuro e legível (corrige bug de contraste)."""
    return ft.TextField(
        label=label,
        hint_text=hint,
        value=value,
        password=password,
        can_reveal_password=password,
        width=width,
        border_radius=10,
        filled=True,
        bgcolor=COR_CARD,
        color=COR_TEXTO,                       # texto digitado (escuro)
        cursor_color=COR_PRIMARIA,
        border_color=COR_BORDA,
        focused_border_color=COR_PRIMARIA,
        label_style=ft.TextStyle(color=COR_TEXTO_SUAVE),
        hint_style=ft.TextStyle(color=COR_TEXTO_SUAVE),
    )


def botao_primario(texto, on_click, width=220, icone=None):
    return ft.ElevatedButton(
        texto,
        icon=icone,
        on_click=on_click,
        bgcolor=COR_PRIMARIA,
        color="white",
        width=width,
        height=46,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
    )


def botao_perigo(texto, on_click, width=130, icone=None):
    return ft.ElevatedButton(
        texto,
        icon=icone,
        on_click=on_click,
        bgcolor=COR_ERRO,
        color="white",
        width=width,
        height=40,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
    )


def card(conteudo, padding=20):
    """Card branco com bordas arredondadas e sombra suave."""
    return ft.Container(
        content=conteudo,
        padding=padding,
        bgcolor=COR_CARD,
        border_radius=14,
        shadow=ft.BoxShadow(blur_radius=8, color="#0F172A12"),
    )


def card_usuario(u, on_detalhe, on_deletar):
    icones = {
        "locatario":     ft.Icons.PERSON,
        "locador":       ft.Icons.BUSINESS,
        "administrador": ft.Icons.ADMIN_PANEL_SETTINGS,
    }
    cores = {
        "locatario":     COR_PRIMARIA,
        "locador":       "#6A1B9A",
        "administrador": "#B71C1C",
    }
    tipo = u.get("tipo", "usuario")

    return ft.Container(
        content=ft.Row(
            [
                ft.Icon(icones.get(tipo, ft.Icons.PERSON), color=cores.get(tipo, COR_TEXTO), size=32),
                ft.Column(
                    [
                        ft.Text(u["nome"], weight=ft.FontWeight.BOLD, size=15, color=COR_TEXTO),
                        ft.Text(f"ID: {u['id']}  •  {tipo.capitalize()}", size=12, color=COR_TEXTO_SUAVE),
                    ],
                    spacing=2,
                    expand=True,
                ),
                ft.Row([
                    ft.IconButton(ft.Icons.INFO_OUTLINE, tooltip="Detalhes", on_click=on_detalhe, icon_color=COR_PRIMARIA),
                    ft.IconButton(ft.Icons.DELETE_OUTLINE, tooltip="Deletar", on_click=on_deletar, icon_color=COR_ERRO),
                ]),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=ft.Padding(16, 12, 16, 12),
        margin=ft.Margin(0, 0, 0, 10),
        bgcolor=COR_CARD,
        border_radius=12,
        shadow=ft.BoxShadow(blur_radius=6, color="#0F172A12"),
    )


def card_placeholder(icone, titulo, descricao):
    """Card moderno para telas ainda não integradas ao backend."""
    return ft.Container(
        content=ft.Column(
            [
                ft.Icon(icone, color=COR_PRIMARIA, size=40),
                ft.Text(titulo, weight=ft.FontWeight.BOLD, size=16, color=COR_TEXTO),
                ft.Text(descricao, size=13, color=COR_TEXTO_SUAVE),
            ],
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.START,
        ),
        padding=20,
        bgcolor=COR_CARD,
        border_radius=14,
        shadow=ft.BoxShadow(blur_radius=8, color="#0F172A12"),
        col={"sm": 12, "md": 6, "lg": 4},
    )


def cabecalho_tela(titulo, acoes=None):
    """Linha de cabeçalho padrão: título à esquerda, ações à direita."""
    return ft.Column([
        ft.Row(
            [titulo_secao(titulo), ft.Row(acoes or [])],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        ft.Divider(height=1, color=COR_BORDA),
    ], spacing=8)
