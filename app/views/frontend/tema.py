"""Paleta de cores e tema global da aplicação.

Cores definidas no Contexto do projeto. O tema global, somado às cores explícitas
do helper `campo()` (em componentes.py), corrige o bug de contraste em que o texto
digitado ficava claro sobre fundo claro (ilegível).
"""

import flet as ft

# Paleta oficial (Contexto.txt)
COR_AZUL_ESCURO = "#0F172A"  # navegação / cabeçalhos
COR_AZUL_MEDIO  = "#1E3A8A"  # primária (botões, destaques)
COR_VERDE       = "#10B981"  # sucesso / acento
COR_FUNDO       = "#F8FAFC"  # fundo da aplicação
COR_CARD        = "#FFFFFF"  # fundo de cards/campos
COR_TEXTO       = "#1F2937"  # texto principal (escuro, legível)

# Apoio
COR_TEXTO_SUAVE = "#64748B"
COR_BORDA       = "#CBD5E1"
COR_ERRO        = "#DC2626"
COR_AVISO       = "#D97706"
COR_SUCESSO     = COR_VERDE

# Aliases de papel para uso nas telas
COR_PRIMARIA   = COR_AZUL_MEDIO
COR_SECUNDARIA = COR_AZUL_ESCURO


def aplicar_tema(page: ft.Page):
    """Configura tema, fundo e densidade visual da página."""
    page.bgcolor = COR_FUNDO
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=COR_PRIMARIA,
            secondary=COR_VERDE,
            surface=COR_FUNDO,
            on_surface=COR_TEXTO,
        ),
    )
