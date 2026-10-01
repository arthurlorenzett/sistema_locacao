"""Telas do perfil Locador: CRUD de espaços, agenda (bloqueios) e reservas recebidas."""

from datetime import datetime, time, timedelta

import flet as ft

from frontend import agenda
from frontend.api_client import (
    api_meus_espacos, api_criar_espaco, api_editar_espaco, api_desativar_espaco,
    api_reservas_recebidas, api_bloqueios, api_bloquear, api_remover_bloqueio,
)
from frontend.componentes import (
    cabecalho_tela, card, card_espaco, campo, snack, icone_modalidade,
)
from frontend.tema import (
    COR_PRIMARIA, COR_SECUNDARIA, COR_TEXTO, COR_TEXTO_SUAVE, COR_CARD,
    COR_ERRO, COR_AVISO, COR_SUCESSO,
)
from frontend.telas.locatario import _card_reserva

_MODALIDADES = ["Futebol", "Futsal", "Tênis", "Vôlei", "Basquete", "Beach Tênis"]
_DIAS = ("Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo")
# Opções de horário de 30 em 30 minutos, de 00:00 até 24:00 (meia-noite).
_HORAS = [f"{m // 60:02d}:{m % 60:02d}" for m in range(0, 24 * 60 + 1, 30)]


def tela_meus_espacos(page: ft.Page):
    raiz = ft.Container(expand=True)
    grade = ft.ResponsiveRow(run_spacing=16, spacing=16)

    def carregar():
        dados, code = api_meus_espacos()
        grade.controls.clear()
        if code != 200:
            grade.controls.append(ft.Text(dados.get("erro", "Erro ao carregar espaços."), color=COR_ERRO))
        else:
            espacos = dados.get("espacos", [])
            if not espacos:
                grade.controls.append(ft.Text("Você ainda não cadastrou espaços.", color=COR_TEXTO_SUAVE))
            for esp in espacos:
                grade.controls.append(card_espaco(
                    esp, on_reservar=None,
                    acoes_extra=[
                        ft.IconButton(ft.Icons.EDIT, icon_color=COR_SECUNDARIA, tooltip="Editar",
                                      on_click=_capt(esp, lambda e, x: mostrar_form(x))),
                        ft.IconButton(ft.Icons.EVENT_BUSY, icon_color=COR_AVISO, tooltip="Bloquear horários",
                                      on_click=_capt(esp, lambda e, x: mostrar_bloqueios(x))),
                        ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=COR_ERRO, tooltip="Desativar",
                                      on_click=_capt(esp, lambda e, x: _desativar(page, x["id"], carregar))),
                    ],
                ))
        page.update()

    def mostrar_lista():
        raiz.content = ft.Column([
            cabecalho_tela("Meus Espaços", acoes=[
                ft.ElevatedButton("Novo espaço", icon=ft.Icons.ADD_BUSINESS,
                                  on_click=lambda e: mostrar_form(None),
                                  bgcolor=COR_PRIMARIA, color="white"),
            ]),
            ft.Container(content=grade, padding=ft.Padding(0, 12, 0, 0)),
        ], spacing=8, scroll=ft.ScrollMode.AUTO)
        carregar()
        page.update()

    def mostrar_form(espaco):
        raiz.content = _form_espaco(page, espaco, on_voltar=mostrar_lista, ao_salvar=mostrar_lista)
        page.update()

    def mostrar_bloqueios(espaco):
        raiz.content = _tela_bloqueios(page, espaco, on_voltar=mostrar_lista)
        page.update()

    mostrar_lista()
    return raiz


def _form_espaco(page, espaco, on_voltar, ao_salvar):
    edicao = espaco is not None
    e = espaco or {}

    f_nome = campo("Nome do espaço", width=320, value=e.get("nome", ""))
    f_modalidade = ft.Dropdown(label="Modalidade", width=200,
                               value=e.get("tipo_esporte") or e.get("modalidade"),
                               options=[ft.dropdown.Option(m) for m in _MODALIDADES])
    f_tipo_quadra = campo("Tipo de quadra", width=200, value=e.get("tipo_quadra") or "")
    f_preco = campo("Preço por hora", width=160, value=str(e.get("preco_hora") or ""))
    f_regiao = campo("Região", width=240, value=e.get("regiao") or "")
    f_endereco = campo("Endereço", width=320, value=e.get("endereco") or "")
    f_foto = campo("URL da foto (opcional)", width=320, value=e.get("foto_url") or "")
    f_descricao = campo("Descrição", width=320, value=e.get("descricao") or "")
    c_online = ft.Checkbox(label="Aceita pagamento online", value=e.get("aceita_online", True))
    c_presencial = ft.Checkbox(label="Aceita pagamento presencial", value=e.get("aceita_presencial", True))
    editor_horarios, coletar_horarios = _editor_horarios(page, e.get("horarios"))

    def salvar(_):
        if not (f_nome.value or "").strip() or not f_modalidade.value:
            snack(page, "Nome e modalidade são obrigatórios.", COR_AVISO)
            return
        try:
            horarios = coletar_horarios()
        except ValueError as erro:
            snack(page, str(erro), COR_AVISO)
            return
        payload = {
            "nome": f_nome.value.strip(),
            "modalidade": f_modalidade.value,
            "tipo_quadra": (f_tipo_quadra.value or "").strip(),
            "preco_hora": (f_preco.value or "").strip(),
            "regiao": (f_regiao.value or "").strip(),
            "endereco": (f_endereco.value or "").strip(),
            "foto_url": (f_foto.value or "").strip(),
            "descricao": (f_descricao.value or "").strip(),
            "aceita_online": c_online.value,
            "aceita_presencial": c_presencial.value,
            "horarios": horarios,
        }
        if edicao:
            dados, code = api_editar_espaco(e["id"], payload)
            ok = code == 200
        else:
            dados, code = api_criar_espaco(payload)
            ok = code == 201
        if ok:
            snack(page, dados.get("mensagem", "Espaço salvo!"), COR_SUCESSO)
            ao_salvar()
        else:
            snack(page, dados.get("erro", "Não foi possível salvar."), COR_ERRO)

    return ft.Column([
        ft.TextButton("Voltar", icon=ft.Icons.ARROW_BACK, on_click=lambda e: on_voltar()),
        cabecalho_tela("Editar espaço" if edicao else "Novo espaço"),
        card(ft.Column([
            ft.ResponsiveRow([
                ft.Container(f_nome, col={"sm": 12, "md": 6}),
                ft.Container(f_modalidade, col={"sm": 6, "md": 3}),
                ft.Container(f_tipo_quadra, col={"sm": 6, "md": 3}),
                ft.Container(f_preco, col={"sm": 6, "md": 3}),
                ft.Container(f_regiao, col={"sm": 6, "md": 4}),
                ft.Container(f_endereco, col={"sm": 12, "md": 5}),
                ft.Container(f_foto, col={"sm": 12, "md": 6}),
                ft.Container(f_descricao, col={"sm": 12, "md": 6}),
            ], spacing=10, run_spacing=10),
            ft.Row([c_online, c_presencial], spacing=20),
            ft.Divider(height=16),
            editor_horarios,
            ft.ElevatedButton("Salvar", icon=ft.Icons.SAVE, on_click=salvar,
                              bgcolor=COR_PRIMARIA, color="white", height=44),
        ], spacing=12)),
    ], spacing=8, scroll=ft.ScrollMode.AUTO)


def _dropdown_hora(valor, desabilitado=False):
    """Seletor de horário de 30 em 30 minutos (00:00 a 24:00)."""
    return ft.Dropdown(value=valor, width=110, dense=True, menu_height=300, disabled=desabilitado,
                       options=[ft.dropdown.Option(h) for h in _HORAS])


def _editor_horarios(page, horarios):
    """Grade semanal editável: um dia por linha (marcar = aberto) com abertura e fechamento.

    Devolve (controle, coletar); `coletar()` devolve a lista no formato da API ou
    levanta ValueError com uma mensagem para o usuário.
    """
    existentes = {h["dia_semana"]: h for h in (horarios or [])}
    linhas = []  # (checkbox, dropdown_abre, dropdown_fecha)

    def _ao_marcar(abre, fecha):
        def handler(ev):
            abre.disabled = fecha.disabled = not ev.control.value
            page.update()
        return handler

    for dia, nome in enumerate(_DIAS):
        h = existentes.get(dia)
        # Espaço sem grade (novo ou antigo): sugere todos os dias abertos das 08:00 às 22:00.
        aberto = bool(h) if existentes else True
        abre = _dropdown_hora(h["abre"] if h else "08:00", not aberto)
        fecha = _dropdown_hora(h["fecha"] if h else "22:00", not aberto)
        chk = ft.Checkbox(label=nome, value=aberto, width=120, on_change=_ao_marcar(abre, fecha))
        linhas.append((chk, abre, fecha))

    def repetir_segunda(_):
        _, abre_seg, fecha_seg = linhas[0]
        for chk, abre, fecha in linhas[1:]:
            if chk.value:
                abre.value, fecha.value = abre_seg.value, fecha_seg.value
        page.update()

    def coletar():
        grade = []
        for dia, (chk, abre, fecha) in enumerate(linhas):
            if not chk.value:
                continue
            # "HH:MM" com zero à esquerda: a comparação de texto equivale à de horário.
            if not abre.value or not fecha.value or fecha.value <= abre.value:
                raise ValueError(f"{_DIAS[dia]}: o fechamento deve ser depois da abertura.")
            grade.append({"dia_semana": dia, "abre": abre.value, "fecha": fecha.value})
        if not grade:
            raise ValueError("Marque ao menos um dia de funcionamento.")
        return grade

    controle = ft.Column([
        ft.Row([
            ft.Text("Horário de funcionamento", size=15, weight=ft.FontWeight.BOLD, color=COR_TEXTO),
            ft.TextButton("Repetir o horário de segunda nos dias marcados",
                          icon=ft.Icons.COPY_ALL, on_click=repetir_segunda),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True),
        ft.Text("Desmarque os dias em que o espaço fica fechado. 24:00 = meia-noite.",
                size=12, color=COR_TEXTO_SUAVE),
        *[ft.Row([chk, abre, ft.Text("às", color=COR_TEXTO_SUAVE), fecha],
                 spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER)
          for chk, abre, fecha in linhas],
    ], spacing=6)
    return controle, coletar


def _tela_bloqueios(page, espaco, on_voltar):
    """Agenda do espaço: bloqueia um dia inteiro ou uma faixa de horário e lista os bloqueios ativos."""
    hoje = agenda.hoje()
    estado = {"dia": hoje}
    lista = ft.Column(spacing=8)
    txt_dia = ft.Text(size=14, weight=ft.FontWeight.W_600, color=COR_TEXTO)
    c_dia_inteiro = ft.Checkbox(label="Dia inteiro", value=True)
    f_inicio = _dropdown_hora("08:00", desabilitado=True)
    f_fim = _dropdown_hora("12:00", desabilitado=True)
    f_motivo = campo("Motivo (só você vê)", hint="Ex.: manutenção do gramado", width=360)

    def mostrar_dia():
        txt_dia.value = f"{agenda.rotulo_dia(estado['dia'], hoje)} ({estado['dia']:%d/%m/%Y})"

    def ao_marcar_dia_inteiro(e):
        f_inicio.disabled = f_fim.disabled = c_dia_inteiro.value
        page.update()

    c_dia_inteiro.on_change = ao_marcar_dia_inteiro

    def ao_escolher_data(e):
        valor = e.control.value
        if valor:
            estado["dia"] = valor.date() if isinstance(valor, datetime) else valor
            mostrar_dia()
            page.update()

    def abrir_calendario(_):
        # Um seletor novo a cada abertura: show_dialog recusa um diálogo que já está na pilha.
        page.show_dialog(ft.DatePicker(
            value=datetime.combine(estado["dia"], time()),
            first_date=datetime.combine(hoje, time()),
            last_date=datetime.combine(hoje + timedelta(days=365), time()),
            help_text="Dia do bloqueio", cancel_text="Cancelar", confirm_text="OK",
            on_change=ao_escolher_data,
        ))

    def carregar():
        dados, code = api_bloqueios(espaco["id"])
        lista.controls.clear()
        if code != 200:
            lista.controls.append(ft.Text(dados.get("erro", "Erro ao carregar bloqueios."), color=COR_ERRO))
        elif not dados.get("bloqueios"):
            lista.controls.append(ft.Text(
                "Nenhum bloqueio ativo: a agenda segue o horário de funcionamento.", color=COR_TEXTO_SUAVE))
        for b in dados.get("bloqueios", []) if code == 200 else []:
            lista.controls.append(ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.EVENT_BUSY, color=COR_AVISO, size=26),
                    ft.Column([
                        ft.Text(agenda.descrever_bloqueio(b), weight=ft.FontWeight.BOLD, size=14, color=COR_TEXTO),
                        ft.Text(b.get("motivo") or "Sem motivo informado", size=12, color=COR_TEXTO_SUAVE),
                    ], spacing=2, expand=True),
                    ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=COR_ERRO, tooltip="Remover bloqueio",
                                  on_click=_capt(b, lambda e, x: remover(x))),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=COR_CARD, border_radius=12, padding=ft.Padding(16, 10, 8, 10),
                shadow=ft.BoxShadow(blur_radius=6, color="#1118271A"),
            ))
        page.update()

    def bloquear(_):
        payload = {"motivo": (f_motivo.value or "").strip()}
        if c_dia_inteiro.value:
            payload.update(data=estado["dia"].isoformat(), dia_inteiro=True)
        else:
            # "HH:MM" com zero à esquerda: a comparação de texto equivale à de horário.
            if not f_inicio.value or not f_fim.value or f_fim.value <= f_inicio.value:
                snack(page, "O fim do bloqueio deve ser depois do início.", COR_AVISO)
                return
            payload["inicio"], payload["fim"] = agenda.periodo_faixa(estado["dia"], f_inicio.value, f_fim.value)
        dados, code = api_bloquear(espaco["id"], payload)
        if code == 201:
            snack(page, dados.get("mensagem", "Horário bloqueado."), COR_SUCESSO)
            f_motivo.value = ""
            carregar()
        else:
            snack(page, dados.get("erro", "Não foi possível bloquear."), COR_ERRO)

    def remover(bloqueio):
        dados, code = api_remover_bloqueio(espaco["id"], bloqueio["id"])
        if code == 200:
            snack(page, dados.get("mensagem", "Bloqueio removido."), COR_SUCESSO)
            carregar()
        else:
            snack(page, dados.get("erro", "Não foi possível remover."), COR_ERRO)

    mostrar_dia()
    formulario = card(ft.Column([
        ft.Text("Novo bloqueio", size=15, weight=ft.FontWeight.BOLD, color=COR_TEXTO),
        ft.Row([txt_dia, ft.OutlinedButton("Escolher data", icon=ft.Icons.CALENDAR_MONTH,
                                           on_click=abrir_calendario)], spacing=12, wrap=True),
        c_dia_inteiro,
        ft.Row([f_inicio, ft.Text("às", color=COR_TEXTO_SUAVE), f_fim], spacing=10,
               vertical_alignment=ft.CrossAxisAlignment.CENTER),
        f_motivo,
        ft.ElevatedButton("Bloquear", icon=ft.Icons.BLOCK, on_click=bloquear,
                          bgcolor=COR_ERRO, color="white", height=42),
    ], spacing=10))

    carregar()
    return ft.Column([
        ft.TextButton("Voltar", icon=ft.Icons.ARROW_BACK, on_click=lambda e: on_voltar()),
        cabecalho_tela(f"Agenda — {espaco.get('nome', '')}"),
        ft.Text("Horários bloqueados deixam de aparecer para os clientes e não aceitam reservas. "
                "Para bloquear um período que já tem reserva, cancele a reserva antes.",
                size=13, color=COR_TEXTO_SUAVE),
        formulario,
        ft.Text("Bloqueios ativos", size=15, weight=ft.FontWeight.BOLD, color=COR_TEXTO),
        lista,
    ], spacing=10, scroll=ft.ScrollMode.AUTO)


def _desativar(page, espaco_id, recarregar):
    dados, code = api_desativar_espaco(espaco_id)
    if code == 200:
        snack(page, dados.get("mensagem", "Espaço desativado."), COR_SUCESSO)
        recarregar()
    else:
        snack(page, dados.get("erro", "Não foi possível desativar."), COR_ERRO)


def _capt(espaco, fn):
    return lambda e: fn(e, espaco)


def tela_reservas_recebidas(page: ft.Page):
    lista = ft.Column(spacing=10)

    def carregar():
        dados, code = api_reservas_recebidas()
        lista.controls.clear()
        if code != 200:
            lista.controls.append(ft.Text(dados.get("erro", "Erro ao carregar."), color=COR_ERRO))
        else:
            reservas = dados.get("reservas", [])
            if not reservas:
                lista.controls.append(ft.Text("Nenhuma reserva recebida ainda.", color=COR_TEXTO_SUAVE))
            for r in reservas:
                lista.controls.append(_card_reserva(page, r, carregar,
                                                    permitir_cancelar=True, permitir_confirmar=True))
        page.update()

    carregar()
    return ft.Column([cabecalho_tela("Reservas Recebidas"),
                      ft.Container(lista, padding=ft.Padding(0, 12, 0, 0))],
                     spacing=8, scroll=ft.ScrollMode.AUTO)
