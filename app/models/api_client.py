"""import requests

class ApiClient:
    def __init__(self):
        self.base_url = "http://localhost:5000"

    def cadastrar_usuario(self, payload):
        try:
            r = requests.post(f"{self.base_url}/usuarios", json=payload, timeout=5)
            return r.json(), r.status_code
        except requests.exceptions.ConnectionError:
            return {"erro": "Sem conexão com o servidor."}, 0 """
#teste para ver se o arquivo é necessário, caso não seja, pode ser deletado.