"""
Ponto de entrada principal da aplicação.
Importa a fábrica do aplicativo Flask e inicia o servidor de desenvolvimento.
"""

from app import create_app

# Cria a instância do aplicativo configurado
app = create_app()

if __name__ == '__main__':
    # Roda o servidor na porta 5000 com o modo de depuração (debug) ativado
    app.run(debug=True)