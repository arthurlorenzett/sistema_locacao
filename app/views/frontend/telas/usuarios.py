"""Telas de gestão de usuários (perfil administrador): listar, cadastrar e editar."""

import flet as ft

from frontend.api_client import api_get, api_post, api_put, api_delete
from frontend.componentes import (
    campo, botao_primario, botao_perigo, card_usuario, snack, cabecalho_tela,
)
from frontend.tema import COR_PRIMARIA, COR_TEXTO_SUAVE, COR_ERRO, COR_AVISO, COR_SUCESSO


# ─────────────────────────── LISTAR / GERENCIAR ───────────────────────────

def tela_usuarios(page: ft.Page):
    lista_view = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=0, expand=True)
    status_txt = ft.Text("", size=13, color=COR_TEXTO_SUAVE)

    def fechar_dlg(dlg):
        dlg.open = False
        page.update()

    def carregar():
        lista_view.controls.clear()
        dados, code = api_get("/usuarios")
        if code != 200:
            status_txt.value = dados.get("erro", "Erro ao carregar.")
            lista_view.controls.append(ft.Text(dados.get("erro", "Erro"), color=COR_ERRO))
        else:
            usuarios = dados.get("usuarios", [])
            status_txt.value = f"{dados.get('total_usuarios', 0)} usuário(s) cadastrado(s)"
            if not usuarios:
                lista_view.controls.append(ft.Text("Nenhum usuário cadastrado.", color=COR_TEXTO_SUAVE))
            for u in usuarios:
                uid, nome = u["id"], u["nome"]
                lista_view.controls.append(
                    card_usuario(
                        u,
                        on_detalhe=lambda e, i=uid: abrir_detalhe(i),
                        on_deletar=lambda e, i=uid, n=nome: confirmar_deletar(i, n),
                    )
                )
        page.update()

    def abrir_detalhe(uid):
        dados, code = api_get(f"/usuarios/{uid}")
        if code != 200:
            snack(page, dados.get("erro", "Erro"), COR_ERRO)
            return

        extras = []
        if dados.get("cpf"):
            extras.append(ft.Text(f"CPF: {dados['cpf']}", size=13))
        if dados.get("cnpj"):
            extras.append(ft.Text(f"CNPJ: {dados['cnpj']}", size=13))
        if dados.get("razao_social"):
            extras.append(ft.Text(f"Razão Social: {dados['razao_social']}", size=13))

        dlg = ft.AlertDialog(
            title=ft.Text(dados["nome"], weight=ft.FontWeight.BOLD),
            content=ft.Column(
                [
                    ft.Text(f"ID: {dados['id']}", size=13, color=COR_TEXTO_SUAVE),
                    ft.Text(f"Email: {dados['email']}", size=13),
                    ft.Text(f"Tipo: {dados['tipo'].capitalize()}", size=13),
                    *extras,
                ],
                spacing=6,
                tight=True,
            ),
            actions=[ft.TextButton("Fechar", on_click=lambda e: fechar_dlg(dlg))],
        )
        page.dialog = dlg
        dlg.open = True
        page.update()

    def confirmar_deletar(uid, nome):
        def executar(e):
            resp, code = api_delete(f"/usuarios/{uid}")
            fechar_dlg(dlg)
            if code == 200:
                snack(page, f"Usuário '{nome}' deletado.")
                carregar()
            else:
                snack(page, resp.get("erro", "Erro ao deletar."), COR_ERRO)

        dlg = ft.AlertDialog(
            title=ft.Text("Confirmar exclusão"),
            content=ft.Text(f"Deseja excluir '{nome}'? Esta ação não pode ser desfeita."),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: fechar_dlg(dlg)),
                botao_perigo("Deletar", executar, width=110),
            ],
        )
        page.dialog = dlg
        dlg.open = True
        page.update()

    carregar()

    return ft.Column(
        [
            cabecalho_tela(
                "Usuários",
                acoes=[
                    status_txt,
                    ft.IconButton(ft.Icons.REFRESH, tooltip="Recarregar",
                                  on_click=lambda e: carregar(), icon_color=COR_PRIMARIA),
                ],
            ),
            ft.Container(lista_view, expand=True, padding=ft.Padding(0, 8, 0, 0)),
        ],
        expand=True,
        spacing=8,
    )


# ─────────────────────────── CADASTRAR ───────────────────────────

def tela_cadastro(page: ft.Page):
    tipo_dd = ft.Dropdown(
        label="Tipo de usuário",
        width=320,
        border_radius=10,
        options=[
            ft.dropdown.Option("locatario", "Locatário"),
            ft.dropdown.Option("locador", "Locador (Empresa)"),
            ft.dropdown.Option("administrador", "Administrador"),
        ],
        value="locatario",
    )

    f_nome  = campo("Nome completo")
    f_email = campo("E-mail")
    f_senha = campo("Senha", password=True)
    f_cpf   = campo("CPF (ex: 123.456.789-00)")
    f_cnpj  = campo("CNPJ")
    f_razao = campo("Razão Social")

    campos_locatario = ft.Column([f_cpf], visible=True, spacing=12)
    campos_locador   = ft.Column([f_cnpj, f_razao], visible=False, spacing=12)

    def on_tipo_change(e):
        campos_locatario.visible = tipo_dd.value == "locatario"
        campos_locador.visible   = tipo_dd.value == "locador"
        page.update()

    tipo_dd.on_change = on_tipo_change

    def cadastrar(e):
        payload = {
            "tipo":  tipo_dd.value,
            "nome":  (f_nome.value or "").strip(),
            "email": (f_email.value or "").strip(),
            "senha": f_senha.value or "",
        }
        if tipo_dd.value == "locatario":
            payload["cpf"] = (f_cpf.value or "").strip()
        elif tipo_dd.value == "locador":
            payload["cnpj"]         = (f_cnpj.value or "").strip()
            payload["razao_social"] = (f_razao.value or "").strip()

        if not payload["nome"] or not payload["email"] or not payload["senha"]:
            snack(page, "Preencha nome, e-mail e senha.", COR_AVISO)
            return

        resp, code = api_post("/usuarios", payload)
        if code == 201:
            snack(page, resp.get("mensagem", "Cadastrado com sucesso!"))
            for f in (f_nome, f_email, f_senha, f_cpf, f_cnpj, f_razao):
                f.value = ""
            page.update()
        else:
            snack(page, resp.get("erro", "Erro ao cadastrar."), COR_ERRO)

    return ft.Column(
        [
            cabecalho_tela("Cadastrar Usuário"),
            ft.Container(
                content=ft.Column(
                    [
                        tipo_dd, f_nome, f_email, f_senha,
                        campos_locatario, campos_locador,
                        ft.Container(height=4),
                        botao_primario("Cadastrar", cadastrar, icone=ft.Icons.PERSON_ADD),
                    ],
                    spacing=12,
                ),
                padding=ft.Padding(0, 16, 0, 0),
            ),
        ],
        spacing=8,
        scroll=ft.ScrollMode.AUTO,
    )


# ─────────────────────────── EDITAR ───────────────────────────

def tela_editar(page: ft.Page):
    f_id    = campo("ID do usuário", width=140)
    f_nome  = campo("Novo nome")
    f_email = campo("Novo e-mail")
    f_senha = campo("Nova senha", password=True)
    resultado = ft.Text("", size=13)

    def buscar(e):
        ident = (f_id.value or "").strip()
        if not ident.isdigit():
            snack(page, "Informe um ID válido.", COR_AVISO)
            return
        dados, code = api_get(f"/usuarios/{ident}")
        if code == 200:
            f_nome.value  = dados.get("nome", "")
            f_email.value = dados.get("email", "")
            resultado.value = f"Usuário encontrado: {dados['tipo'].capitalize()}"
            resultado.color = COR_SUCESSO
        else:
            resultado.value = dados.get("erro", "Não encontrado.")
            resultado.color = COR_ERRO
        page.update()

    def salvar(e):
        ident = (f_id.value or "").strip()
        if not ident.isdigit():
            snack(page, "Informe um ID válido.", COR_AVISO)
            return
        payload = {}
        if (f_nome.value or "").strip():  payload["nome"]  = f_nome.value.strip()
        if (f_email.value or "").strip(): payload["email"] = f_email.value.strip()
        if (f_senha.value or "").strip(): payload["senha"] = f_senha.value.strip()

        if not payload:
            snack(page, "Altere ao menos um campo.", COR_AVISO)
            return

        resp, code = api_put(f"/usuarios/{ident}", payload)
        if code == 200:
            snack(page, "Usuário atualizado com sucesso!")
        else:
            snack(page, resp.get("erro", "Erro ao atualizar."), COR_ERRO)

    return ft.Column(
        [
            cabecalho_tela("Editar Usuário"),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row([f_id, botao_primario("Buscar", buscar, width=130, icone=ft.Icons.SEARCH)], spacing=10),
                        resultado,
                        f_nome, f_email, f_senha,
                        ft.Text("Deixe em branco os campos que não deseja alterar.",
                                size=12, color=COR_TEXTO_SUAVE),
                        botao_primario("Salvar alterações", salvar, icone=ft.Icons.SAVE),
                    ],
                    spacing=12,
                ),
                padding=ft.Padding(0, 16, 0, 0),
            ),
        ],
        spacing=8,
        scroll=ft.ScrollMode.AUTO,
    )
