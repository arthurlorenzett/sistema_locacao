"""Tela de detalhe de um espaço esportivo (aberta a partir da busca)."""

import flet as ft

from frontend.componentes import card, estrelas_avaliacao, icone_modalidade
from frontend.tema import (
    COR_PRIMARIA, COR_SECUNDARIA, COR_TEXTO, COR_TEXTO_SUAVE, COR_CARD,
)


def _info(icone, rotulo, valor):
    return ft.Row([
        ft.Icon(icone, size=18, color=COR_SECUNDARIA),
        ft.Text(f"{rotulo}: ", size=14, weight=ft.FontWeight.W_600, color=COR_TEXTO),
        ft.Text(valor or "—", size=14, color=COR_TEXTO_SUAVE),
    ], spacing=6)


def view_detalhe(page: ft.Page, espaco: dict, on_voltar, on_reservar):
    """Constrói o conteúdo de detalhe. `on_voltar`/`on_reservar` são callbacks."""
    modalidade = espaco.get("modalidade") or espaco.get("tipo_esporte") or ""
    preco = espaco.get("preco_hora", 0)

    if espaco.get("foto_url"):
        topo = ft.Container(
            content=ft.Image(src=espaco["foto_url"], fit="cover", expand=True),
            height=220, border_radius=14, clip_behavior=ft.ClipBehavior.ANTI_ALIAS)
    else:
        topo = ft.Container(
            content=ft.Icon(icone_modalidade(modalidade), size=80, color="white"),
            height=220, bgcolor=COR_SECUNDARIA, alignment=ft.alignment.center, border_radius=14)

    pagamentos = []
    if espaco.get("aceita_online", True):
        pagamentos.append("Online")
    if espaco.get("aceita_presencial", True):
        pagamentos.append("Presencial")

    detalhes = card(ft.Column([
        ft.Row([
            ft.Text(espaco.get("nome", "—"), size=24, weight=ft.FontWeight.BOLD, color=COR_TEXTO),
            ft.Container(expand=True),
            ft.Text(f"R$ {preco:.0f}/hora", size=20, weight=ft.FontWeight.BOLD, color=COR_SECUNDARIA),
        ]),
        estrelas_avaliacao(espaco.get("nota_media")) if espaco.get("nota_media") else ft.Container(),
        ft.Divider(),
        _info(ft.Icons.SPORTS, "Modalidade", modalidade),
        _info(ft.Icons.SPORTS_TENNIS, "Tipo de quadra", espaco.get("tipo_quadra")),
        _info(ft.Icons.LOCATION_ON_OUTLINED, "Endereço", espaco.get("endereco")),
        _info(ft.Icons.MAP_OUTLINED, "Região", espaco.get("regiao")),
        _info(ft.Icons.PAYMENTS_OUTLINED, "Pagamento", " / ".join(pagamentos) or "—"),
        ft.Text(espaco.get("descricao") or "", size=14, color=COR_TEXTO_SUAVE),
        ft.Container(height=8),
        ft.ElevatedButton("Reservar Agora", icon=ft.Icons.CALENDAR_MONTH,
                          on_click=lambda e: on_reservar(), bgcolor=COR_PRIMARIA, color="white",
                          height=46, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))),
    ], spacing=10))

    return ft.Column([
        ft.TextButton("Voltar", icon=ft.Icons.ARROW_BACK, on_click=lambda e: on_voltar()),
        topo,
        ft.Container(height=8),
        detalhes,
    ], spacing=8, scroll=ft.ScrollMode.AUTO)
