"""Componentes visuais reutilizáveis.

Centraliza a criação de campos, botões, cards e feedback (SnackBar) para manter
padronização visual e evitar duplicação entre as telas.
"""

import flet as ft

from frontend.tema import (
    COR_PRIMARIA, COR_SECUNDARIA, COR_ESCURO, COR_CARD, COR_TEXTO, COR_TEXTO_SUAVE,
    COR_BORDA, COR_ERRO, COR_SUCESSO, COR_AVISO,
)


# Ícones grandes por modalidade esportiva.
_ICONES_MODALIDADE = {
    "futebol": ft.Icons.SPORTS_SOCCER,
    "futsal": ft.Icons.SPORTS_SOCCER,
    "society": ft.Icons.SPORTS_SOCCER,
    "tênis": ft.Icons.SPORTS_TENNIS,
    "tenis": ft.Icons.SPORTS_TENNIS,
    "beach tênis": ft.Icons.SPORTS_TENNIS,
    "beach tenis": ft.Icons.SPORTS_TENNIS,
    "vôlei": ft.Icons.SPORTS_VOLLEYBALL,
    "volei": ft.Icons.SPORTS_VOLLEYBALL,
    "vôlei de praia": ft.Icons.SPORTS_VOLLEYBALL,
    "basquete": ft.Icons.SPORTS_BASKETBALL,
    "handebol": ft.Icons.SPORTS_HANDBALL,
}


def icone_modalidade(modalidade):
    """Devolve um ícone grande e reconhecível para a modalidade informada."""
    chave = (modalidade or "").strip().lower()
    return _ICONES_MODALIDADE.get(chave, ft.Icons.SPORTS)


def estrelas_avaliacao(nota, tamanho=16):
    """Linha de estrelas (0-5) com a nota numérica ao lado."""
    nota = float(nota or 0)
    estrelas = []
    for i in range(1, 6):
        if nota >= i:
            ic = ft.Icons.STAR
        elif nota >= i - 0.5:
            ic = ft.Icons.STAR_HALF
        else:
            ic = ft.Icons.STAR_BORDER
        estrelas.append(ft.Icon(ic, color=COR_AVISO, size=tamanho))
    if nota > 0:
        estrelas.append(ft.Text(f"{nota:.1f}", size=tamanho - 3, color=COR_TEXTO_SUAVE))
    return ft.Row(estrelas, spacing=1, tight=True)


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


def _linha_info(icone, texto):
    return ft.Row([ft.Icon(icone, size=15, color=COR_TEXTO_SUAVE),
                   ft.Text(texto, size=13, color=COR_TEXTO_SUAVE)], spacing=5, tight=True)


def card_espaco(espaco, on_reservar=None, on_detalhe=None, on_favoritar=None,
                favorito=False, acoes_extra=None):
    """Card de espaço no estilo da referência (imagem topo, infos e CTA verde).

    `espaco` é o dict serializado pela API. Callbacks recebem o evento Flet.
    """
    modalidade = espaco.get("modalidade") or espaco.get("tipo_esporte") or ""
    preco = espaco.get("preco_hora")
    preco_txt = f"R$ {preco:.0f}/hora" if isinstance(preco, (int, float)) else "—"
    nota = espaco.get("nota_media")

    # Topo: imagem ou ícone da modalidade + badge.
    if espaco.get("foto_url"):
        topo_visual = ft.Container(
            content=ft.Image(src=espaco["foto_url"], fit="cover", expand=True),
            height=140, clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            border_radius=ft.BorderRadius(
                top_left=14, top_right=14,
                bottom_left=0,
                bottom_right=0,
            )
    )
    else:
        topo_visual = ft.Container(
            content=ft.Icon(icone_modalidade(modalidade), size=54, color="white"),
            height=140, bgcolor=COR_SECUNDARIA, alignment=ft.Alignment(0, 0),
           border_radius=ft.BorderRadius(top_left=14, top_right=14, bottom_left=0, bottom_right=0),
        )

    badge = ft.Container(
        content=ft.Text("Disponível Hoje", size=11, color="white", weight=ft.FontWeight.W_600),
        bgcolor=COR_PRIMARIA, padding=ft.Padding(8, 3, 8, 3), border_radius=8,
    ) if espaco.get("disponivel", True) else ft.Container()

    topo = ft.Stack([topo_visual, ft.Container(content=badge, padding=8)], height=140)

    linha_rating = estrelas_avaliacao(nota) if nota else ft.Row(
        [ft.Icon(icone_modalidade(modalidade), size=16, color=COR_SECUNDARIA),
         ft.Text(modalidade, size=12, color=COR_TEXTO_SUAVE)], spacing=5, tight=True)

    botoes = []
    if on_reservar:
        botoes.append(ft.ElevatedButton(
            "Reservar Agora", icon=ft.Icons.CALENDAR_MONTH, on_click=on_reservar,
            bgcolor=COR_PRIMARIA, color="white", expand=True, height=42,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))))
    if on_favoritar:
        botoes.append(ft.IconButton(
            ft.Icons.FAVORITE if favorito else ft.Icons.FAVORITE_BORDER,
            on_click=on_favoritar, icon_color=COR_ERRO, tooltip="Favoritar"))
    for a in (acoes_extra or []):
        botoes.append(a)

    corpo = ft.Column([
        ft.Text(espaco.get("nome", "—"), weight=ft.FontWeight.BOLD, size=16, color=COR_TEXTO),
        linha_rating,
        _linha_info(ft.Icons.LOCATION_ON_OUTLINED, espaco.get("endereco") or espaco.get("regiao") or "Local não informado"),
        _linha_info(ft.Icons.SPORTS, f"{modalidade}" + (f" • {espaco.get('tipo_quadra')}" if espaco.get("tipo_quadra") else "")),
        ft.Row([ft.Text(preco_txt, weight=ft.FontWeight.BOLD, size=15, color=COR_SECUNDARIA),
                ft.Container(expand=True),
                ft.Text(espaco.get("distancia") or "", size=12, color=COR_TEXTO_SUAVE)]),
        ft.Row(botoes, spacing=4),
    ], spacing=7)

    card_container = ft.Container(
        content=ft.Column([topo, ft.Container(content=corpo, padding=14)], spacing=0),
        bgcolor=COR_CARD, border_radius=14,
        shadow=ft.BoxShadow(blur_radius=8, color="#1118271A"),
        width=300,
        on_click=on_detalhe,
        col={"sm": 12, "md": 6, "lg": 4},
    )
    return card_container


def faixa_estatisticas(itens):
    """Faixa verde com métricas (lista de tuplas (valor, rotulo))."""
    colunas = []
    for valor, rotulo in itens:
        colunas.append(ft.Column(
            [ft.Text(str(valor), size=26, weight=ft.FontWeight.BOLD, color="white"),
             ft.Text(rotulo, size=12, color="white")],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2, expand=True,
        ))
    return ft.Container(
        content=ft.Row(colunas, alignment=ft.MainAxisAlignment.SPACE_AROUND),
        bgcolor=COR_PRIMARIA, padding=ft.Padding(24, 28, 24, 28), border_radius=14,
    )
