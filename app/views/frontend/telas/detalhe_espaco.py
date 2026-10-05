"""Tela de detalhe de um espaço esportivo (aberta a partir da busca)."""

import flet as ft

from frontend.api_client import api_avaliacoes
from frontend.componentes import (
    card, estrelas_avaliacao, icone_modalidade, resumo_horarios, data_br, texto_total_avaliacoes,
    texto_preco, resumo_regras_preco, moeda,
)
from frontend.tema import (
    COR_PRIMARIA, COR_SECUNDARIA, COR_TEXTO, COR_TEXTO_SUAVE, COR_CARD,
)


def _info(icone, rotulo, valor):
    return ft.Row([
        ft.Icon(icone, size=18, color=COR_SECUNDARIA),
        ft.Text(f"{rotulo}: ", size=14, weight=ft.FontWeight.W_600, color=COR_TEXTO),
        ft.Text(valor or "—", size=14, color=COR_TEXTO_SUAVE),
    ], spacing=6)


def _bloco_horarios(horarios):
    linhas = resumo_horarios(horarios)
    if not linhas:
        return _info(ft.Icons.SCHEDULE, "Horários", "Não informado")
    return ft.Row([
        ft.Icon(ft.Icons.SCHEDULE, size=18, color=COR_SECUNDARIA),
        ft.Text("Horários: ", size=14, weight=ft.FontWeight.W_600, color=COR_TEXTO),
        ft.Column([ft.Text(l, size=14, color=COR_TEXTO_SUAVE) for l in linhas], spacing=2),
    ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.START)


def _bloco_precos(espaco):
    """Preço padrão e as regras por horário (só aparece se o espaço tiver regras)."""
    regras = espaco.get("regras_preco")
    if not regras:
        return []
    linhas = [f"Padrão: {moeda(espaco.get('preco_hora') or 0)}/hora", *resumo_regras_preco(regras)]
    return [ft.Row([
        ft.Icon(ft.Icons.SELL_OUTLINED, size=18, color=COR_SECUNDARIA),
        ft.Text("Preços: ", size=14, weight=ft.FontWeight.W_600, color=COR_TEXTO),
        ft.Column([ft.Text(l, size=14, color=COR_TEXTO_SUAVE) for l in linhas], spacing=2),
    ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.START)]


def _bloco_avaliacoes(espaco_id):
    """Média, total e os comentários mais recentes do espaço."""
    dados, code = api_avaliacoes(espaco_id)
    titulo = ft.Text("Avaliações", size=18, weight=ft.FontWeight.BOLD, color=COR_TEXTO)
    if code != 200:
        return card(ft.Column([titulo, ft.Text(dados.get("erro", "Não foi possível carregar as avaliações."),
                                               size=13, color=COR_TEXTO_SUAVE)], spacing=8))
    if not dados.get("total"):
        return card(ft.Column([titulo, ft.Text("Este espaço ainda não foi avaliado.",
                                               size=13, color=COR_TEXTO_SUAVE)], spacing=8))

    itens = []
    for a in dados.get("avaliacoes", []):
        itens.append(ft.Column([
            ft.Row([estrelas_avaliacao(a["nota"], tamanho=14),
                    ft.Text(f"{a.get('autor') or 'Cliente'} · {data_br(a.get('data'))}",
                            size=12, color=COR_TEXTO_SUAVE)], spacing=8),
            *([ft.Text(a["comentario"], size=14, color=COR_TEXTO)] if a.get("comentario") else []),
        ], spacing=2))
        itens.append(ft.Divider(height=12))
    return card(ft.Column([
        ft.Row([titulo, estrelas_avaliacao(dados.get("media"), tamanho=18),
                ft.Text(texto_total_avaliacoes(dados["total"]), size=13, color=COR_TEXTO_SUAVE)],
               spacing=10, wrap=True, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        *itens[:-1],
    ], spacing=8))


def view_detalhe(page: ft.Page, espaco: dict, on_voltar, on_reservar):
    """Constrói o conteúdo de detalhe. `on_voltar`/`on_reservar` são callbacks."""
    modalidade = espaco.get("modalidade") or espaco.get("tipo_esporte") or ""

    if espaco.get("foto_url"):
        topo = ft.Container(
            image=ft.DecorationImage(src=espaco["foto_url"], fit=ft.BoxFit.COVER),
            height=220, border_radius=14, bgcolor=COR_SECUNDARIA)
    else:
        topo = ft.Container(
            content=ft.Icon(icone_modalidade(modalidade), size=80, color="white"),
            height=220, bgcolor=COR_SECUNDARIA, alignment=ft.Alignment.CENTER, border_radius=14)

    pagamentos = []
    if espaco.get("aceita_online", True):
        pagamentos.append("Online")
    if espaco.get("aceita_presencial", True):
        pagamentos.append("Presencial")

    detalhes = card(ft.Column([
        ft.Row([
            ft.Text(espaco.get("nome", "—"), size=24, weight=ft.FontWeight.BOLD, color=COR_TEXTO),
            ft.Container(expand=True),
            ft.Text(texto_preco(espaco), size=20, weight=ft.FontWeight.BOLD, color=COR_SECUNDARIA),
        ]),
        estrelas_avaliacao(espaco.get("nota_media")) if espaco.get("nota_media") else ft.Container(),
        ft.Divider(),
        _info(ft.Icons.SPORTS, "Modalidade", modalidade),
        _info(ft.Icons.SPORTS_TENNIS, "Tipo de quadra", espaco.get("tipo_quadra")),
        _info(ft.Icons.LOCATION_ON_OUTLINED, "Endereço", espaco.get("endereco")),
        _info(ft.Icons.MAP_OUTLINED, "Região", espaco.get("regiao")),
        _info(ft.Icons.PAYMENTS_OUTLINED, "Pagamento", " / ".join(pagamentos) or "—"),
        _bloco_horarios(espaco.get("horarios")),
        *_bloco_precos(espaco),
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
        _bloco_avaliacoes(espaco["id"]),
    ], spacing=8, scroll=ft.ScrollMode.AUTO)
