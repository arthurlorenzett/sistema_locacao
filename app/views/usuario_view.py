import flet as ft
from controllers.usuario_controller import UsuarioController

class TelaCadastroView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.controller = UsuarioController() # Instancia o Controller

        # Aqui ficam os seus campos ft.TextField (f_nome, f_email, etc)
        self.f_nome = ft.TextField(label="Nome")
        self.f_email = ft.TextField(label="E-mail")
        # ... outros campos ...

    def botao_cadastrar_click(self, e):
        # A View pergunta pro Controller: Salva isso pra mim?
        sucesso, mensagem = self.controller.salvar_novo_usuario(
            tipo="locatario", # Exemplo simplificado
            nome=self.f_nome.value,
            email=self.f_email.value,
            senha="123",
            cpf="111.222.333-44"
        )

        # O Controller respondeu. A View só mostra na tela:
        cor = "green" if sucesso else "red"
        self.page.snack_bar = ft.SnackBar(content=ft.Text(mensagem), bgcolor=cor)
        self.page.snack_bar.open = True
        self.page.update()

    def renderizar(self):
        return ft.Column([
            self.f_nome,
            self.f_email,
            ft.ElevatedButton("Cadastrar", on_click=self.botao_cadastrar_click)
        ])