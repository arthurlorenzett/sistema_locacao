from app.models.usuario_model import Locador, Locatario, Administrador

class UsuarioFactory:
    """Fábrica responsável por instanciar diferentes tipos de usuários. Implementa Factory Method."""
    
    @staticmethod
    def criar_usuario(tipo, nome, email, senha, **kwargs):
        if tipo == 'locatario':
            cpf = kwargs.get('cpf') # Obtém o CPF dos argumentos adicionais
            if not cpf:
                raise ValueError("Locatário requer CPF.")
            return Locatario(nome=nome, email=email, senha=senha, cpf=cpf)
        
        elif tipo == 'locador':
            cnpj = kwargs.get('cnpj')
            razao_social = kwargs.get('razao_social')
            
            if not cnpj or not razao_social:
                raise ValueError("Locador requer CNPJ e Razão Social.")
                
            return Locador(nome=nome, email=email, senha=senha, cnpj=cnpj, razao_social=razao_social)
        
        elif tipo == 'administrador':
            return Administrador(nome=nome, email=email, senha=senha)
        
        else:
            raise ValueError(f"Tipo de usuário '{tipo}' desconhecido.")