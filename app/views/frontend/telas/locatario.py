"""Telas do perfil Locatário: busca de espaços com filtros, detalhe, reserva e
minhas reservas — no estilo da referência "Arena Fácil"."""

import flet as ft

from frontend import agenda
from frontend.api_client import (
    api_listar_espacos, api_disponibilidade, api_reservar, api_confirmar_reserva,
    api_minhas_reservas, api_cancelar_reserva, api_registrar_comparecimento,
    api_favoritos, api_favoritar, api_desfavoritar,
)
from frontend.componentes import (
    cabecalho_tela, card, card_espaco, faixa_estatisticas, campo, snack, estrelas_avaliacao,
    icone_modalidade, descricao_confianca,
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
_DURACOES = {"1": "1 hora", "2": "2 horas", "3": "3 horas"}
# Por que um horário aparece desativado na grade do diálogo de reserva.
_MOTIVOS = {"passado": "Horário já passou", "reservado": "Já reservado",
            "bloqueado": "Indisponível (fechado pelo local)"}
_COR_SELECAO = "#A7F3D0"  # verde claro para o dia/horário escolhido


def dialogo_reserva(page: ft.Page, espaco: dict, ao_sucesso=None):
    """Diálogo de reserva: escolhe o dia, um horário livre, a duração e o pagamento."""
    dia_hoje = agenda.hoje()
    estado = {"dia": dia_hoje, "horarios": [], "indice": None}
    preco = float(espaco.get("preco_hora") or 0)

    linha_dias = ft.Row(spacing=6, scroll=ft.ScrollMode.AUTO)
    grade_horarios = ft.Row(spacing=6, run_spacing=6, wrap=True)
    info_dia = ft.Text("Carregando horários...", size=12, color=COR_TEXTO_SUAVE)
    resumo = ft.Text("", size=13, weight=ft.FontWeight.W_600, color=COR_SECUNDARIA)
    f_duracao = ft.Dropdown(label="Duração", value="1", width=140, dense=True,
                            options=[ft.dropdown.Option(k, v) for k, v in _DURACOES.items()])

    opcoes = []
    if espaco.get("aceita_online", True):
        opcoes.append(ft.Radio(value="online", label="Pagamento online"))
    if espaco.get("aceita_presencial", True):
        opcoes.append(ft.Radio(value="presencial", label="Pagamento presencial"))
    if not opcoes:
        opcoes.append(ft.Radio(value="presencial", label="Pagamento presencial"))
    grupo = ft.RadioGroup(content=ft.Column(opcoes, spacing=2), value=opcoes[0].value)

    def atualizar_resumo():
        i, horarios = estado["indice"], estado["horarios"]
        if i is None:
            resumo.value = ""
            return
        horas = int(f_duracao.value or 1)
        if not agenda.pode_reservar(horarios, i, horas):
            resumo.value = f"Não há {_DURACOES[str(horas)]} livres seguidas a partir das {horarios[i]['inicio']}."
            resumo.color = COR_AVISO
            return
        fim = horarios[i + horas - 1]["fim"]
        resumo.value = (f"{agenda.rotulo_dia(estado['dia'], dia_hoje)} · {horarios[i]['inicio']}–{fim}"
                        f" · R$ {preco * horas:.0f}")
        resumo.color = COR_SECUNDARIA

    def desenhar():
        linha_dias.controls = [
            ft.Chip(label=ft.Text(agenda.rotulo_dia(d, dia_hoje)), selected=d == estado["dia"],
                    show_checkmark=False, selected_color=_COR_SELECAO, on_select=_escolher_dia(d))
            for d in agenda.proximos_dias(dia_hoje)
        ]
        grade_horarios.controls = [
            ft.Chip(label=ft.Text(h["inicio"]), selected=i == estado["indice"], show_checkmark=False,
                    selected_color=_COR_SELECAO, disabled=not h["disponivel"],
                    tooltip=_MOTIVOS.get(h.get("motivo")), on_select=_escolher_horario(i))
            for i, h in enumerate(estado["horarios"])
        ]
        atualizar_resumo()
        page.update()

    def carregar_dia(dia):
        estado.update(dia=dia, indice=None)
        dados, code = api_disponibilidade(espaco["id"], dia.isoformat())
        estado["horarios"] = dados.get("horarios", []) if code == 200 else []
        if code != 200:
            info_dia.value = dados.get("erro", "Não foi possível carregar os horários.")
        elif not estado["horarios"]:
            info_dia.value = "O espaço fica fechado neste dia."
        elif not any(h["disponivel"] for h in estado["horarios"]):
            info_dia.value = "Nenhum horário livre neste dia."
        else:
            info_dia.value = f"Funcionamento: {dados.get('funcionamento')}. Toque em um horário livre."
        desenhar()

    def _escolher_dia(dia):
        return lambda e: carregar_dia(dia)

    def _escolher_horario(indice):
        def handler(e):
            estado["indice"] = indice
            desenhar()
        return handler

    def ao_mudar_duracao(e):
        atualizar_resumo()
        page.update()

    f_duracao.on_select = ao_mudar_duracao

    def fechar(_=None):
        # Fecha este diálogo especificamente (pop_dialog fecharia um SnackBar aberto por cima).
        dlg.open = False
        dlg.update()

    def confirmar(_):
        i, horas = estado["indice"], int(f_duracao.value or 1)
        if i is None:
            snack(page, "Escolha um horário livre.", COR_AVISO)
            return
        if not agenda.pode_reservar(estado["horarios"], i, horas):
            snack(page, resumo.value, COR_AVISO)
            return
        inicio, fim = agenda.periodo_reserva(estado["dia"], estado["horarios"], i, horas)
        dados, code = api_reservar(espaco["id"], inicio, fim)
        if code != 201:
            snack(page, dados.get("erro", "Não foi possível reservar."), COR_ERRO)
            carregar_dia(estado["dia"])  # o horário pode ter sido ocupado nesse meio tempo
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
            ft.Text(f"{espaco.get('modalidade') or espaco.get('tipo_esporte')} · R$ {preco:.0f}/hora",
                    size=13, color=COR_TEXTO_SUAVE),
            ft.Text("Dia", size=13, weight=ft.FontWeight.W_600, color=COR_TEXTO),
            linha_dias,
            ft.Text("Horário de início", size=13, weight=ft.FontWeight.W_600, color=COR_TEXTO),
            info_dia,
            grade_horarios,
            f_duracao,
            resumo,
            ft.Text("Forma de pagamento", size=13, weight=ft.FontWeight.W_600, color=COR_TEXTO),
            grupo,
        ], tight=True, spacing=10, width=480, scroll=ft.ScrollMode.AUTO),
        actions=[
            ft.TextButton("Cancelar", on_click=fechar),
            ft.ElevatedButton("Confirmar reserva", on_click=confirmar,
                              bgcolor=COR_PRIMARIA, color="white"),
        ],
    )
    page.show_dialog(dlg)
    carregar_dia(dia_hoje)


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
    f_preco_min = campo("Preço mín. (R$)", width=150)
    f_preco_max = campo("Preço máx. (R$)", width=150)
    c_livre_hoje = ft.Checkbox(label="Só com horário livre hoje", value=False)
    filtros_tela = [
        ft.Container(f_local, col={"sm": 12, "md": 4}),
        ft.Container(f_data, col={"sm": 6, "md": 3}),
        ft.Container(f_esporte, col={"sm": 6, "md": 2}),
        ft.Container(f_periodo, col={"sm": 6, "md": 3}),
        ft.Container(f_preco_min, col={"sm": 6, "md": 3}),
        ft.Container(f_preco_max, col={"sm": 6, "md": 3}),
        ft.Container(c_livre_hoje, col={"sm": 12, "md": 4}),
    ]

    def carregar(_=None):
        filtros = {
            "regiao": (f_local.value or "").strip(),
            "modalidade": f_esporte.value or "",
            "data": (f_data.value or "").strip(),
            "preco_min": _valor(f_preco_min),
            "preco_max": _valor(f_preco_max),
        }
        if f_periodo.value:
            filtros["hora"] = _PERIODOS.get(f_periodo.value, "")
        if c_livre_hoje.value:
            filtros["disponivel_hoje"] = "1"
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
                    on_favoritar=alternar_favorito(page, esp),
                    favorito=esp.get("favorito", False),
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
            _hero(carregar, filtros_tela),
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


def _valor(campo_preco):
    """Texto do campo de preço aceitando vírgula decimal (ex.: "80,50")."""
    return (campo_preco.value or "").strip().replace(",", ".")


def _hero(on_buscar, filtros):
    """Título + barra de busca; `filtros` são os campos já com a coluna responsiva definida."""
    barra = card(ft.Column([
        ft.Text("Encontre sua próxima partida", size=15, weight=ft.FontWeight.BOLD, color=COR_TEXTO),
        ft.ResponsiveRow(filtros, spacing=10, run_spacing=10),
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


def alternar_favorito(page, espaco, ao_remover=None):
    """Handler do coração: favorita/desfavorita e troca o ícone no próprio botão."""
    def handler(e):
        if espaco.get("favorito"):
            dados, code = api_desfavoritar(espaco["id"])
            ok = code == 200
        else:
            dados, code = api_favoritar(espaco["id"])
            ok = code in (200, 201)
        if not ok:
            snack(page, dados.get("erro", "Não foi possível atualizar os favoritos."), COR_ERRO)
            return
        espaco["favorito"] = not espaco.get("favorito")
        e.control.icon = ft.Icons.FAVORITE if espaco["favorito"] else ft.Icons.FAVORITE_BORDER
        e.control.update()
        snack(page, dados.get("mensagem", "Favoritos atualizados."), COR_SUCESSO)
        if not espaco["favorito"] and ao_remover:
            ao_remover()
    return handler


def tela_favoritos(page: ft.Page):
    """Espaços favoritados pelo locatário, com reserva e detalhe a um clique."""
    raiz = ft.Container(expand=True)
    grade = ft.ResponsiveRow(run_spacing=16, spacing=16)

    def carregar():
        dados, code = api_favoritos()
        grade.controls.clear()
        if code != 200:
            grade.controls.append(_aviso(dados.get("erro", "Erro ao carregar favoritos.")))
        else:
            espacos = dados.get("espacos", [])
            if not espacos:
                grade.controls.append(_aviso(
                    "Você ainda não tem favoritos. Toque no coração de um espaço na busca para guardá-lo aqui."))
            for esp in espacos:
                grade.controls.append(card_espaco(
                    esp,
                    on_reservar=_fazer(esp, lambda e, x: dialogo_reserva(page, x, ao_sucesso=carregar)),
                    on_detalhe=_fazer(esp, lambda e, x: abrir_detalhe(x)),
                    on_favoritar=alternar_favorito(page, esp, ao_remover=carregar),
                    favorito=True,
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
            cabecalho_tela("Meus Favoritos"),
            ft.Container(content=grade, padding=ft.Padding(0, 12, 0, 12)),
        ], spacing=8, scroll=ft.ScrollMode.AUTO)
        carregar()

    mostrar_lista()
    return raiz


def _aviso(texto):
    return ft.Container(
        content=ft.Text(texto, size=14, color=COR_TEXTO_SUAVE),
        padding=20, col={"sm": 12},
    )


def _fazer(espaco, fn):
    """Captura o espaço atual no closure (evita o clássico bug de late binding)."""
    return lambda e: fn(e, espaco)


# --------- Minhas Reservas ---------

_CORES_STATUS = {"Pendente": COR_AVISO, "Confirmada": COR_SUCESSO, "Cancelada": COR_ERRO,
                 "Concluída": "#047857", "Não compareceu": "#9F1239"}


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


def _card_reserva(page, r, recarregar, permitir_cancelar=False, permitir_confirmar=False,
                  visao_locador=False):
    """Card de uma reserva. `visao_locador` mostra o cliente e o índice de comparecimento dele."""
    status = r.get("status", "Pendente")
    cor = _CORES_STATUS.get(status, COR_TEXTO_SUAVE)

    acoes = []
    if permitir_confirmar and status == "Pendente":
        acoes.append(ft.ElevatedButton("Confirmar", icon=ft.Icons.CHECK,
                     on_click=lambda e: _confirmar_recebida(page, r["id"], recarregar),
                     bgcolor=COR_PRIMARIA, color="white", height=38))
    if r.get("pode_registrar_comparecimento"):
        acoes.append(ft.ElevatedButton("Compareceu", icon=ft.Icons.HOW_TO_REG,
                     on_click=lambda e: _registrar_comparecimento(page, r["id"], True, recarregar),
                     bgcolor=COR_PRIMARIA, color="white", height=38))
        acoes.append(ft.OutlinedButton("Não compareceu", icon=ft.Icons.PERSON_OFF,
                     on_click=lambda e: _confirmar_falta(page, r, recarregar)))
    if permitir_cancelar and r.get("pode_cancelar"):
        acoes.append(ft.OutlinedButton("Cancelar", icon=ft.Icons.CLOSE,
                     on_click=lambda e: _cancelar(page, r["id"], recarregar)))

    quando = agenda.descrever_periodo(r["data_horario"], r.get("data_fim")) if r.get("data_horario") else "—"
    linhas = [
        ft.Text(r.get("espaco_nome") or f"Espaço #{r.get('espaco_id')}",
                weight=ft.FontWeight.BOLD, size=15, color=COR_TEXTO),
        ft.Text(quando, size=12, color=COR_TEXTO_SUAVE),
        ft.Text(f"Pagamento: {r.get('status_pagamento') or '—'}"
                + (f" ({r.get('metodo_pagamento')})" if r.get('metodo_pagamento') else ""),
                size=12, color=COR_TEXTO_SUAVE),
    ]
    if visao_locador:
        texto_confianca, cor_confianca = descricao_confianca(r.get("confianca"))
        linhas.insert(1, ft.Row([
            ft.Icon(ft.Icons.PERSON, size=14, color=COR_TEXTO_SUAVE),
            ft.Text(r.get("locatario_nome") or "Cliente", size=12, weight=ft.FontWeight.W_600, color=COR_TEXTO),
            ft.Text("·", size=12, color=COR_TEXTO_SUAVE),
            ft.Text(texto_confianca, size=12, color=cor_confianca),
        ], spacing=4, tight=True, wrap=True))

    return ft.Container(
        content=ft.Row([
            ft.Icon(icone_modalidade(r.get("espaco_modalidade")), color=COR_SECUNDARIA, size=30),
            ft.Column(linhas, spacing=2, expand=True),
            ft.Container(content=ft.Text(status, color="white", size=12, weight=ft.FontWeight.W_600),
                         bgcolor=cor, padding=ft.Padding(10, 4, 10, 4), border_radius=8),
            ft.Row(acoes, spacing=6),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=COR_CARD, border_radius=12, padding=ft.Padding(16, 12, 16, 12),
        shadow=ft.BoxShadow(blur_radius=6, color="#1118271A"),
    )


def _registrar_comparecimento(page, reserva_id, compareceu, recarregar):
    dados, code = api_registrar_comparecimento(reserva_id, compareceu)
    if code == 200:
        snack(page, dados.get("mensagem", "Comparecimento registrado."), COR_SUCESSO)
        recarregar()
    else:
        snack(page, dados.get("erro", "Não foi possível registrar."), COR_ERRO)


def _confirmar_falta(page, r, recarregar):
    """Registrar falta não tem volta e pesa no histórico do cliente: pede confirmação."""
    def fechar(_=None):
        dlg.open = False
        dlg.update()

    def registrar(_):
        fechar()
        _registrar_comparecimento(page, r["id"], False, recarregar)

    dlg = ft.AlertDialog(
        title=ft.Text("Registrar falta?"),
        content=ft.Text(f"{r.get('locatario_nome') or 'O cliente'} não compareceu a esta reserva? "
                        "A falta entra no histórico de comparecimento dele e não pode ser desfeita."),
        actions=[
            ft.TextButton("Voltar", on_click=fechar),
            ft.ElevatedButton("Registrar falta", on_click=registrar, bgcolor=COR_ERRO, color="white"),
        ],
    )
    page.show_dialog(dlg)


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
