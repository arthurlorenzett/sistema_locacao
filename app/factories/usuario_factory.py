from app.models.usuario_model import Locador, Locatario, Administrador

class UsuarioFactory:
    """Fábrica responsável por instanciar diferentes tipos de usuários. Implementa Factory Method."""
    
    @staticmethod
    def criar_usuario(tipo, nome, email, senha, **kwargs):
        if not nome or not email or not senha:
            raise ValueError("Nome, e-mail e senha são obrigatórios.")

        if tipo == 'locatario':
            cpf = kwargs.get('cpf') # Obtém o CPF dos argumentos adicionais
            if not cpf:
                raise ValueError("Locatário requer CPF.")
            usuario = Locatario(nome=nome, email=email, cpf=cpf)

        elif tipo == 'locador':
            cnpj = kwargs.get('cnpj')
            razao_social = kwargs.get('razao_social')

            if not cnpj or not razao_social:
                raise ValueError("Locador requer CNPJ e Razão Social.")

            usuario = Locador(nome=nome, email=email, cnpj=cnpj, razao_social=razao_social)

        elif tipo == 'administrador':
            usuario = Administrador(nome=nome, email=email)

        else:
            raise ValueError(f"Tipo de usuário '{tipo}' desconhecido.")

        # Senha sempre armazenada como hash (nunca em texto puro).
        usuario.definir_senha(senha)
        return usuario