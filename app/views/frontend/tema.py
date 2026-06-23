"""Paleta de cores e tema global da aplicação ("Arena Fácil").

Paleta verde definida no projeto (#10B981 / #059669 / #111827) + apoio em cinzas.
O tema global, somado às cores explícitas do helper `campo()` (componentes.py),
mantém o texto digitado escuro e legível sobre fundo claro.
"""

import flet as ft

# Paleta oficial (verde)
COR_PRIMARIA    = "#10B981"  # verde principal (botões, destaques)
COR_SECUNDARIA  = "#059669"  # verde escuro (hover/ações fortes)
COR_ESCURO      = "#111827"  # quase-preto (navbar, textos fortes)
COR_VERDE       = COR_PRIMARIA

COR_FUNDO       = "#F8FAFC"  # fundo da aplicação
COR_CARD        = "#FFFFFF"  # fundo de cards/campos
COR_TEXTO       = "#111827"  # texto principal (escuro, legível)

# Apoio
COR_TEXTO_SUAVE = "#6B7280"  # cinza
COR_BORDA       = "#E5E7EB"
COR_ERRO        = "#DC2626"
COR_AVISO       = "#D97706"
COR_SUCESSO     = COR_PRIMARIA

# Aliases legados (telas antigas importavam COR_AZUL_*); apontam para a paleta verde
# para não quebrar imports existentes.
COR_AZUL_ESCURO = COR_ESCURO
COR_AZUL_MEDIO  = COR_PRIMARIA


def aplicar_tema(page: ft.Page):
    """Configura tema, fundo e densidade visual da página."""
    page.bgcolor = COR_FUNDO
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=COR_PRIMARIA,
            secondary=COR_SECUNDARIA,
            surface=COR_FUNDO,
            on_surface=COR_TEXTO,
        ),
    )
