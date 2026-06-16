"""
Interface Gráfica - Sistema de Locação de Espaços Esportivos
Utiliza Flet (Python) + API Flask no backend.

Para rodar:
    pip install flet requests
    python gui_flet.py
"""

import flet as ft
import requests
from datetime import datetime

# ─────────────────────────────────────────
# CONFIGURAÇÃO
# ─────────────────────────────────────────
API_BASE = "http://localhost:5000"


def api_get(path):
    try:
        r = requests.get(f"{API_BASE}{path}", timeout=5)
        # Tenta ler como JSON
        try:
            return r.json(), r.status_code
        except ValueError:
            # Se não for JSON (for HTML de erro, por exemplo), cai aqui e não quebra o app
            return {"erro": f"Erro inesperado no servidor. Status: {r.status_code}"}, r.status_code
            
    except requests.exceptions.ConnectionError:
        return {"erro": "Não foi possível conectar à API. Verifique se o backend está rodando."}, 0


def api_post(path, data):
    try:
        r = requests.post(f"{API_BASE}{path}", json=data, timeout=5)
        return r.json(), r.status_code
    except requests.exceptions.ConnectionError:
        return {"erro": "Não foi possível conectar à API."}, 0


def api_put(path, data):
    try:
        r = requests.put(f"{API_BASE}{path}", json=data, timeout=5)
        return r.json(), r.status_code
    except requests.exceptions.ConnectionError:
        return {"erro": "Não foi possível conectar à API."}, 0


def api_delete(path):
    try:
        r = requests.delete(f"{API_BASE}{path}", timeout=5)
        return r.json(), r.status_code
    except requests.exceptions.ConnectionError:
        return {"erro": "Não foi possível conectar à API."}, 0


# ─────────────────────────────────────────
# CORES / TEMA
# ─────────────────────────────────────────
COR_PRIMARIA   = "#1565C0"
COR_SECUNDARIA = "#42A5F5"
COR_FUNDO      = "#F5F7FA"
COR_CARD       = "#FFFFFF"
COR_TEXTO      = "#1A1A2E"
COR_SUCESSO    = "#2E7D32"
COR_ERRO       = "#C62828"
COR_AVISO      = "#E65100"


# ─────────────────────────────────────────
# COMPONENTES REUTILIZÁVEIS
# ─────────────────────────────────────────

def snack(page, msg, cor=COR_SUCESSO):
    page.snack_bar = ft.SnackBar(
        content=ft.Text(msg, color="white"),
        bgcolor=cor,
        duration=3000,
    )
    page.snack_bar.open = True
    page.update()


def titulo_secao(texto):
    return ft.Text(texto, size=22, weight=ft.FontWeight.BOLD, color=COR_PRIMARIA)


def campo(label, hint="", password=False, width=280):
    return ft.TextField(
        label=label,
        hint_text=hint,
        password=password,
        can_reveal_password=password,
        border_radius=8,
        width=width,
        border_color=COR_SECUNDARIA,
        focused_border_color=COR_PRIMARIA,
    )


def botao_primario(texto, on_click, width=200):
    return ft.ElevatedButton(
        texto,
        on_click=on_click,
        bgcolor=COR_PRIMARIA,
        color="white",
        width=width,
        height=42,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
    )


def botao_perigo(texto, on_click, width=120):
    return ft.ElevatedButton(
        texto,
        on_click=on_click,
        bgcolor=COR_ERRO,
        color="white",
        width=width,
        height=36,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
    )


def card_usuario(u, on_detalhe, on_deletar):
    icones = {
        "locatario":    ft.Icons.PERSON,
        "locador":      ft.Icons.BUSINESS,
        "administrador": ft.Icons.ADMIN_PANEL_SETTINGS,
    }
    cores = {
        "locatario":    "#1565C0",
        "locador":      "#6A1B9A",
        "administrador": "#B71C1C",
    }
    tipo = u.get("tipo", "usuario")

    return ft.Container(
        content=ft.Row(
            [
                ft.Icon(icones.get(tipo, ft.Icons.PERSON), color=cores.get(tipo, "#333"), size=32),
                ft.Column(
                    [
                        ft.Text(u["nome"], weight=ft.FontWeight.BOLD, size=15, color=COR_TEXTO),
                        ft.Text(f"ID: {u['id']}  •  {tipo.capitalize()}", size=12, color="#666"),
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
        padding=ft.Padding(16,12,16,12),
        margin=ft.Margin(0,0,0,8),
        bgcolor=COR_CARD,
        border_radius=10,
        shadow=ft.BoxShadow(blur_radius=4, color="#00000015"),
    )


# ─────────────────────────────────────────
# TELA: LISTAR / GERENCIAR USUÁRIOS
# ─────────────────────────────────────────

def tela_usuarios(page: ft.Page):
    lista_view = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=0, expand=True)
    status_txt = ft.Text("", size=13, color="#888")

    def carregar():
        lista_view.controls.clear()
        dados, code = api_get("/usuarios")
        if code == 0:
            status_txt.value = dados["erro"]
            lista_view.controls.append(ft.Text(dados["erro"], color=COR_ERRO))
        else:
            usuarios = dados.get("usuarios", [])
            status_txt.value = f"{dados.get('total_usuarios', 0)} usuário(s) cadastrado(s)"
            if not usuarios:
                lista_view.controls.append(ft.Text("Nenhum usuário cadastrado.", color="#888"))
            for u in usuarios:
                uid = u["id"]
                lista_view.controls.append(
                    card_usuario(
                        u,
                        on_detalhe=lambda e, i=uid: abrir_detalhe(i),
                        on_deletar=lambda e, i=uid, n=u["nome"]: confirmar_deletar(i, n),
                    )
                )
        page.update()

    def abrir_detalhe(uid):
        dados, code = api_get(f"/usuarios/{uid}")
        if code != 200:
            snack(page, dados.get("erro", "Erro"), COR_ERRO)
            return

        campos_extras = []
        if dados.get("cpf"):
            campos_extras.append(ft.Text(f"CPF: {dados['cpf']}", size=13))
        if dados.get("cnpj"):
            campos_extras.append(ft.Text(f"CNPJ: {dados['cnpj']}", size=13))
        if dados.get("razao_social"):
            campos_extras.append(ft.Text(f"Razão Social: {dados['razao_social']}", size=13))

        dlg = ft.AlertDialog(
            title=ft.Text(dados["nome"], weight=ft.FontWeight.BOLD),
            content=ft.Column(
                [
                    ft.Text(f"ID: {dados['id']}", size=13, color="#555"),
                    ft.Text(f"Email: {dados['email']}", size=13),
                    ft.Text(f"Tipo: {dados['tipo'].capitalize()}", size=13),
                    *campos_extras,
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
                botao_perigo("Deletar", executar, width=100),
            ],
        )
        page.dialog = dlg
        dlg.open = True
        page.update()

    def fechar_dlg(dlg):
        dlg.open = False
        page.update()

    carregar()

    return ft.Column(
        [
            ft.Row(
                [
                    titulo_secao("Usuários"),
                    ft.Row([
                        status_txt,
                        ft.IconButton(
                            ft.Icons.REFRESH,
                            tooltip="Recarregar",
                            on_click=lambda e: carregar(),
                            icon_color=COR_PRIMARIA,
                        ),
                    ]),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Divider(height=1, color="#E0E0E0"),
            ft.Container(lista_view, expand=True, padding=ft.Padding(0,8,0,0)),
        ],
        expand=True,
        spacing=8,
    )


# ─────────────────────────────────────────
# TELA: CADASTRAR USUÁRIO
# ─────────────────────────────────────────

def tela_cadastro(page: ft.Page):
    tipo_dd = ft.Dropdown(
        label="Tipo de usuário",
        width=280,
        border_radius=8,
        border_color=COR_SECUNDARIA,
        focused_border_color=COR_PRIMARIA,
        options=[
            ft.dropdown.Option("locatario", "Locatário"),
            ft.dropdown.Option("locador", "Locador (Empresa)"),
            ft.dropdown.Option("administrador", "Administrador"),
        ],
        value="locatario",
    )

    f_nome  = campo("Nome completo", width=280)
    f_email = campo("E-mail", width=280)
    f_senha = campo("Senha", password=True, width=280)
    f_cpf   = campo("CPF (ex: 123.456.789-00)", width=280)
    f_cnpj  = campo("CNPJ", width=280)
    f_razao = campo("Razão Social", width=280)

    campos_locatario = ft.Column([f_cpf], visible=True, spacing=10)
    campos_locador   = ft.Column([f_cnpj, f_razao], visible=False, spacing=10)

    def on_tipo_change(e):
        campos_locatario.visible = tipo_dd.value == "locatario"
        campos_locador.visible   = tipo_dd.value == "locador"
        page.update()

    tipo_dd.on_change = on_tipo_change

    def cadastrar(e):
        payload = {
            "tipo":  tipo_dd.value,
            "nome":  f_nome.value.strip(),
            "email": f_email.value.strip(),
            "senha": f_senha.value,
        }
        if tipo_dd.value == "locatario":
            payload["cpf"] = f_cpf.value.strip()
        elif tipo_dd.value == "locador":
            payload["cnpj"]         = f_cnpj.value.strip()
            payload["razao_social"] = f_razao.value.strip()

        if not payload["nome"] or not payload["email"] or not payload["senha"]:
            snack(page, "Preencha nome, e-mail e senha.", COR_AVISO)
            return

        resp, code = api_post("/usuarios", payload)
        if code == 201:
            snack(page, resp.get("mensagem", "Cadastrado com sucesso!"))
            for f in [f_nome, f_email, f_senha, f_cpf, f_cnpj, f_razao]:
                f.value = ""
            page.update()
        else:
            snack(page, resp.get("erro", "Erro ao cadastrar."), COR_ERRO)

    return ft.Column(
        [
            titulo_secao("Cadastrar Usuário"),
            ft.Divider(height=1, color="#E0E0E0"),
            ft.Container(
                content=ft.Column(
                    [
                        tipo_dd,
                        f_nome,
                        f_email,
                        f_senha,
                        campos_locatario,
                        campos_locador,
                        ft.Container(height=4),
                        botao_primario("Cadastrar", cadastrar),
                    ],
                    spacing=12,
                ),
                padding=ft.Padding(0,16,0,0),
            ),
        ],
        spacing=8,
        scroll=ft.ScrollMode.AUTO,
    )


# ─────────────────────────────────────────
# TELA: EDITAR USUÁRIO
# ─────────────────────────────────────────

def tela_editar(page: ft.Page):
    f_id    = campo("ID do usuário", width=120)
    f_nome  = campo("Novo nome", width=280)
    f_email = campo("Novo e-mail", width=280)
    f_senha = campo("Nova senha", password=True, width=280)
    resultado = ft.Text("", size=13)

    def buscar(e):
        if not f_id.value.strip().isdigit():
            snack(page, "Informe um ID válido.", COR_AVISO)
            return
        dados, code = api_get(f"/usuarios/{f_id.value.strip()}")
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
        if not f_id.value.strip().isdigit():
            snack(page, "Informe um ID válido.", COR_AVISO)
            return
        payload = {}
        if f_nome.value.strip():  payload["nome"]  = f_nome.value.strip()
        if f_email.value.strip(): payload["email"] = f_email.value.strip()
        if f_senha.value.strip(): payload["senha"] = f_senha.value.strip()

        if not payload:
            snack(page, "Altere ao menos um campo.", COR_AVISO)
            return

        resp, code = api_put(f"/usuarios/{f_id.value.strip()}", payload)
        if code == 200:
            snack(page, "Usuário atualizado com sucesso!")
        else:
            snack(page, resp.get("erro", "Erro ao atualizar."), COR_ERRO)

    return ft.Column(
        [
            titulo_secao("Editar Usuário"),
            ft.Divider(height=1, color="#E0E0E0"),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row([f_id, botao_primario("Buscar", buscar, width=120)], spacing=10),
                        resultado,
                        f_nome,
                        f_email,
                        f_senha,
                        ft.Text("Deixe em branco os campos que não deseja alterar.", size=12, color="#888"),
                        botao_primario("Salvar alterações", salvar),
                    ],
                    spacing=12,
                ),
                padding=ft.Padding(0,16,0,0),
            ),
        ],
        spacing=8,
        scroll=ft.ScrollMode.AUTO,
    )


# ─────────────────────────────────────────
# TELA: STATUS DA API
# ─────────────────────────────────────────

def tela_status(page: ft.Page):
    conteudo = ft.Column(spacing=8)

    def verificar(e=None):
        conteudo.controls.clear()
        dados, code = api_get("/")
        if code == 0:
            conteudo.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.CLOUD_OFF, color=COR_ERRO, size=32),
                        ft.Column([
                            ft.Text("Backend offline", weight=ft.FontWeight.BOLD, color=COR_ERRO),
                            ft.Text(dados.get("erro", ""), size=12, color="#555"),
                        ], spacing=2),
                    ]),
                    padding=16, bgcolor="#FFEBEE", border_radius=10,
                )
            )
        else:
            conteudo.controls += [
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.CLOUD_DONE, color=COR_SUCESSO, size=32),
                        ft.Column([
                            ft.Text("API online e operacional", weight=ft.FontWeight.BOLD, color=COR_SUCESSO),
                            ft.Text(dados.get("mensagem", ""), size=12, color="#555"),
                        ], spacing=2),
                    ]),
                    padding=16, bgcolor="#E8F5E9", border_radius=10,
                ),
                ft.Container(height=8),
                ft.Text("Informações do sistema:", weight=ft.FontWeight.BOLD, color=COR_TEXTO),
                ft.Text(f"Projeto:  {dados.get('projeto', '-')}", size=13),
                ft.Text(f"Versão:   {dados.get('versao', '-')}", size=13),
                ft.Text(f"Verificado em: {datetime.now().strftime('%H:%M:%S')}", size=12, color="#888"),
            ]
        page.update()

    verificar()

    return ft.Column(
        [
            ft.Row(
                [
                    titulo_secao("Status da API"),
                    ft.IconButton(
                        ft.Icons.REFRESH,
                        tooltip="Verificar novamente",
                        on_click=verificar,
                        icon_color=COR_PRIMARIA,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Divider(height=1, color="#E0E0E0"),
            ft.Container(conteudo, padding=ft.Padding(0,16,0,0)),
        ],
        spacing=8,
    )


# ─────────────────────────────────────────
# APP PRINCIPAL
# ─────────────────────────────────────────

def main(page: ft.Page):
    page.title = "Espaços Esportivos"
    page.bgcolor = COR_FUNDO
    page.window.width  = 860
    page.window.height = 640
    page.padding = 0

    area_conteudo = ft.Container(expand=True, padding=24)

    def navegar(index):
        telas = {
            0: tela_status,
            1: tela_usuarios,
            2: tela_cadastro,
            3: tela_editar,
        }
        area_conteudo.content = telas[index](page)
        page.update()

    nav_rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        bgcolor=COR_PRIMARIA,
        indicator_color=COR_SECUNDARIA,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.MONITOR,
                selected_icon=ft.Icons.MONITOR,
                label="Status",
                padding=ft.Padding(0,4,0,4),
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.PEOPLE_OUTLINED,
                selected_icon=ft.Icons.PEOPLE,
                label="Usuários",
                padding=ft.Padding(0,4,0,4),
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.PERSON_ADD_OUTLINED,
                selected_icon=ft.Icons.PERSON_ADD,
                label="Cadastrar",
                padding=ft.Padding(0,4,0,4),
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.EDIT_OUTLINED,
                selected_icon=ft.Icons.EDIT,
                label="Editar",
                padding=ft.Padding(0,4,0,4),
            ),
        ],
        on_change=lambda e: navegar(e.control.selected_index),
        leading=ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.SPORTS_SOCCER, color="white", size=32),
                ft.Text("Espaços\nEsportivos", color="white", size=11, text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
            padding=ft.Padding(0,16,0,16),
        ),
    )

    page.add(
        ft.Row(
            [
                ft.Container(content=nav_rail, bgcolor=COR_PRIMARIA, width=90),
                ft.VerticalDivider(width=1, color="#E0E0E0"),
                area_conteudo,
            ],
            expand=True,
            spacing=0,
        )
    )

    navegar(0)


ft.run(main)
