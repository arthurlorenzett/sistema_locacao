"""Telas do perfil Locatário: busca de espaços com filtros, detalhe, reserva e
minhas reservas — no estilo da referência "Arena Fácil"."""

import flet as ft

from frontend.api_client import (
    api_listar_espacos, api_reservar, api_confirmar_reserva,
    api_minhas_reservas, api_cancelar_reserva,
)
from frontend.componentes import (
    cabecalho_tela, card, card_espaco, faixa_estatisticas, campo, snack, estrelas_avaliacao,
    icone_modalidade,
)
from frontend.tema import (
    COR_PRIMARIA, COR_SECUNDARIA, COR_TEXTO, COR_TEXTO_SUAVE, COR_CARD,
    COR_ERRO, COR_AVISO, COR_SUCESSO,
)
from frontend.telas.detalhe_espaco import view_detalhe

# Modalidades oferecidas nos filtros (espelha os ícones do componente).
_MODALIDADES = ["Futebol", "Futsal", "Tênis", "Vôlei", "Basquete", "Beach Tênis"]
# Período -> hora representativa usada no filtro de disponibilidade.
_PERIODOS = {"Manhã": "09:00", "Tarde": "14:00", "Noite": "19:00"}


def dialogo_reserva(page: ft.Page, espaco: dict, ao_sucesso=None):
    """Abre o diálogo de reserva (data/hora + método de pagamento)."""
    f_data = campo("Data (AAAA-MM-DD)", width=190)
    f_hora = campo("Hora (HH:MM)", width=130)

    opcoes = []
    if espaco.get("aceita_online", True):
        opcoes.append(ft.Radio(value="online", label="Pagamento online"))
    if espaco.get("aceita_presencial", True):
        opcoes.append(ft.Radio(value="presencial", label="Pagamento presencial"))
    if not opcoes:
        opcoes.append(ft.Radio(value="presencial", label="Pagamento presencial"))
    grupo = ft.RadioGroup(content=ft.Column(opcoes, spacing=2), value=opcoes[0].value)

    def fechar(_=None):
        dlg.open = False
        page.update()

    def confirmar(_):
        data = (f_data.value or "").strip()
        hora = (f_hora.value or "").strip()
        if not data or not hora:
            snack(page, "Informe data e hora.", COR_AVISO)
            return
        dados, code = api_reservar(espaco["id"], f"{data}T{hora}")
        if code != 201:
            snack(page, dados.get("erro", "Não foi possível reservar."), COR_ERRO)
            return
        # Confirma o pagamento (online/presencial) — fluxo de poucos cliques.
        rid = dados.get("reserva_id")
        pdados, pcode = api_confirmar_reserva(rid, grupo.value)
        if pcode == 200:
            snack(page, "Reserva confirmada com sucesso!", COR_SUCESSO)
        else:
            snack(page, pdados.get("erro", "Reserva criada (pague depois)."), COR_AVISO)
        fechar()
        if ao_sucesso:
            ao_sucesso()

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text(f"Reservar — {espaco.get('nome', '')}", color=COR_TEXTO),
        content=ft.Column([
            ft.Text(f"Modalidade: {espaco.get('modalidade') or espaco.get('tipo_esporte')}",
                    size=13, color=COR_TEXTO_SUAVE),
            ft.Text(f"Valor: R$ {espaco.get('preco_hora', 0):.0f}/hora",
                    size=13, color=COR_SECUNDARIA, weight=ft.FontWeight.BOLD),
            ft.Row([f_data, f_hora], spacing=8),
            ft.Text("Forma de pagamento:", size=13, color=COR_TEXTO),
            grupo,
        ], tight=True, spacing=10, width=360),
        actions=[
            ft.TextButton("Cancelar", on_click=fechar),
            ft.ElevatedButton("Confirmar reserva", on_click=confirmar,
                              bgcolor=COR_PRIMARIA, color="white"),
        ],
    )
    page.overlay.append(dlg)
    dlg.open = True
    page.update()


def tela_buscar_espacos(page: ft.Page):
    """Busca de quadras: hero + filtros + grade de cards + estatísticas."""
    raiz = ft.Container(expand=True)
    grade = ft.ResponsiveRow(run_spacing=16, spacing=16)

    f_local = campo("Localização", hint="Digite sua cidade/região", width=240)
    f_data = campo("Data (AAAA-MM-DD)", width=190)
    f_esporte = ft.Dropdown(label="Esporte", width=180,
                            options=[ft.dropdown.Option("")] + [ft.dropdown.Option(m) for m in _MODALIDADES])
    f_periodo = ft.Dropdown(label="Horário", width=150,
                            options=[ft.dropdown.Option("")] + [ft.dropdown.Option(p) for p in _PERIODOS])
    f_preco_max = campo("Preço máx.", width=130)

    def carregar(_=None):
        filtros = {
            "regiao": (f_local.value or "").strip(),
            "modalidade": f_esporte.value or "",
            "data": (f_data.value or "").strip(),
            "preco_max": (f_preco_max.value or "").strip(),
        }
        if f_periodo.value:
            filtros["hora"] = _PERIODOS.get(f_periodo.value, "")
        dados, code = api_listar_espacos(filtros)
        grade.controls.clear()
        if code == 0:
            grade.controls.append(_aviso("Sem conexão com o servidor."))
        elif code != 200:
            grade.controls.append(_aviso(dados.get("erro", "Erro ao buscar espaços.")))
        else:
            espacos = dados.get("espacos", [])
            if not espacos:
                grade.controls.append(_aviso("Nenhum espaço encontrado para os filtros."))
            for esp in espacos:
                grade.controls.append(card_espaco(
                    esp,
                    on_reservar=_fazer(esp, lambda e, x: dialogo_reserva(page, x, ao_sucesso=carregar)),
                    on_detalhe=_fazer(esp, lambda e, x: abrir_detalhe(x)),
                ))
        page.update()

    def abrir_detalhe(espaco):
        raiz.content = view_detalhe(
            page, espaco,
            on_voltar=mostrar_lista,
            on_reservar=lambda: dialogo_reserva(page, espaco, ao_sucesso=mostrar_lista),
        )
        page.update()

    def mostrar_lista():
        raiz.content = ft.Column([
            _hero(carregar, f_local, f_data, f_esporte, f_periodo, f_preco_max),
            ft.Container(height=8),
            cabecalho_tela("Locais Disponíveis"),
            ft.Text("Os espaços esportivos mais bem avaliados da sua região",
                    size=13, color=COR_TEXTO_SUAVE),
            ft.Container(content=grade, padding=ft.Padding(0, 12, 0, 12)),
            faixa_estatisticas([("50.000+", "Reservas realizadas"), ("500+", "Locais cadastrados"),
                                ("100.000+", "Usuários ativos"), ("4.9★", "Avaliação média")]),
        ], spacing=8, scroll=ft.ScrollMode.AUTO)
        carregar()
        page.update()

    mostrar_lista()
    return raiz


def _hero(on_buscar, f_local, f_data, f_esporte, f_periodo, f_preco_max):
    barra = card(ft.Column([
        ft.Text("Encontre sua próxima partida", size=15, weight=ft.FontWeight.BOLD, color=COR_TEXTO),
        ft.ResponsiveRow([
            ft.Container(f_local, col={"sm": 12, "md": 4}),
            ft.Container(f_data, col={"sm": 6, "md": 3}),
            ft.Container(f_esporte, col={"sm": 6, "md": 2}),
            ft.Container(f_periodo, col={"sm": 6, "md": 2}),
            ft.Container(f_preco_max, col={"sm": 6, "md": 2}),
        ], spacing=10, run_spacing=10),
        ft.ElevatedButton("Buscar Quadras", icon=ft.Icons.SEARCH, on_click=on_buscar,
                          bgcolor=COR_PRIMARIA, color="white", height=44,
                          style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))),
    ], spacing=12))

    titulo = ft.Column([
        ft.Text("Reserve sua quadra\nem segundos", size=30, weight=ft.FontWeight.BOLD, color=COR_TEXTO),
        ft.Text("Encontre quadras de futebol, vôlei, tênis e muito mais. "
                "Compare preços, horários disponíveis e reserve online.",
                size=14, color=COR_TEXTO_SUAVE),
    ], spacing=8)

    return ft.Column([titulo, ft.Container(height=8), barra], spacing=4)


def _aviso(texto):
    return ft.Container(
        content=ft.Text(texto, size=14, color=COR_TEXTO_SUAVE),
        padding=20, col={"sm": 12},
    )


def _fazer(espaco, fn):
    """Captura o espaço atual no closure (evita o clássico bug de late binding)."""
    return lambda e: fn(e, espaco)


# --------- Minhas Reservas ---------

_CORES_STATUS = {"Pendente": COR_AVISO, "Confirmada": COR_SUCESSO, "Cancelada": COR_ERRO}


def tela_minhas_reservas(page: ft.Page):
    lista = ft.Column(spacing=10)

    def carregar():
        dados, code = api_minhas_reservas()
        lista.controls.clear()
        if code == 0:
            lista.controls.append(ft.Text("Sem conexão com o servidor.", color=COR_ERRO))
        elif code != 200:
            lista.controls.append(ft.Text(dados.get("erro", "Erro ao carregar."), color=COR_ERRO))
        else:
            reservas = dados.get("reservas", [])
            if not reservas:
                lista.controls.append(ft.Text("Você ainda não possui reservas.", color=COR_TEXTO_SUAVE))
            for r in reservas:
                lista.controls.append(_card_reserva(page, r, carregar, permitir_cancelar=True))
        page.update()

    carregar()
    return ft.Column([cabecalho_tela("Minhas Reservas"), ft.Container(lista, padding=ft.Padding(0, 12, 0, 0))],
                     spacing=8, scroll=ft.ScrollMode.AUTO)


def _card_reserva(page, r, recarregar, permitir_cancelar=False, permitir_confirmar=False):
    status = r.get("status", "Pendente")
    cor = _CORES_STATUS.get(status, COR_TEXTO_SUAVE)

    acoes = []
    if permitir_confirmar and status == "Pendente":
        acoes.append(ft.ElevatedButton("Confirmar", icon=ft.Icons.CHECK,
                     on_click=lambda e: _confirmar_recebida(page, r["id"], recarregar),
                     bgcolor=COR_PRIMARIA, color="white", height=38))
    if permitir_cancelar and status != "Cancelada":
        acoes.append(ft.OutlinedButton("Cancelar", icon=ft.Icons.CLOSE,
                     on_click=lambda e: _cancelar(page, r["id"], recarregar)))

    return ft.Container(
        content=ft.Row([
            ft.Icon(icone_modalidade(r.get("espaco_modalidade")), color=COR_SECUNDARIA, size=30),
            ft.Column([
                ft.Text(r.get("espaco_nome") or f"Espaço #{r.get('espaco_id')}",
                        weight=ft.FontWeight.BOLD, size=15, color=COR_TEXTO),
                ft.Text(f"{(r.get('data_horario') or '').replace('T', ' ')}", size=12, color=COR_TEXTO_SUAVE),
                ft.Text(f"Pagamento: {r.get('status_pagamento') or '—'}"
                        + (f" ({r.get('metodo_pagamento')})" if r.get('metodo_pagamento') else ""),
                        size=12, color=COR_TEXTO_SUAVE),
            ], spacing=2, expand=True),
            ft.Container(content=ft.Text(status, color="white", size=12, weight=ft.FontWeight.W_600),
                         bgcolor=cor, padding=ft.Padding(10, 4, 10, 4), border_radius=8),
            ft.Row(acoes, spacing=6),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=COR_CARD, border_radius=12, padding=ft.Padding(16, 12, 16, 12),
        shadow=ft.BoxShadow(blur_radius=6, color="#1118271A"),
    )


def _cancelar(page, reserva_id, recarregar):
    dados, code = api_cancelar_reserva(reserva_id)
    if code == 200:
        snack(page, dados.get("mensagem", "Reserva cancelada."), COR_SUCESSO)
        recarregar()
    else:
        snack(page, dados.get("erro", "Não foi possível cancelar."), COR_ERRO)


def _confirmar_recebida(page, reserva_id, recarregar):
    dados, code = api_confirmar_reserva(reserva_id, "presencial")
    if code == 200:
        snack(page, dados.get("mensagem", "Reserva confirmada."), COR_SUCESSO)
        recarregar()
    else:
        snack(page, dados.get("erro", "Não foi possível confirmar."), COR_ERRO)
