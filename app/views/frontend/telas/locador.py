"""Telas do perfil Locador: CRUD de espaços e gestão de reservas recebidas."""

import flet as ft

from frontend.api_client import (
    api_meus_espacos, api_criar_espaco, api_editar_espaco, api_desativar_espaco,
    api_reservas_recebidas,
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

    def salvar(_):
        if not (f_nome.value or "").strip() or not f_modalidade.value:
            snack(page, "Nome e modalidade são obrigatórios.", COR_AVISO)
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
            ft.ElevatedButton("Salvar", icon=ft.Icons.SAVE, on_click=salvar,
                              bgcolor=COR_PRIMARIA, color="white", height=44),
        ], spacing=12)),
    ], spacing=8, scroll=ft.ScrollMode.AUTO)


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
