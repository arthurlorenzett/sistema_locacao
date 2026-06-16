from models.api_client import ApiClient

class UsuarioController:
    def __init__(self):
        self.api = ApiClient()

    def salvar_novo_usuario(self, tipo, nome, email, senha, cpf=None, cnpj=None):
        # Regra de negócio pura (sem Flet e sem requests)
        if not nome or not email or not senha:
            return False, "Preencha nome, e-mail e senha."
            
        payload = {"tipo": tipo, "nome": nome, "email": email, "senha": senha}
        if tipo == "locatario": payload["cpf"] = cpf
        if tipo == "locador": payload["cnpj"] = cnpj

        resposta, status = self.api.cadastrar_usuario(payload)
        
        if status == 201:
            return True, resposta.get("mensagem")
        return False, resposta.get("erro", "Erro desconhecido.")