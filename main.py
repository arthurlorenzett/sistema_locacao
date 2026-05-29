from flask import Flask

# Inicializa o aplicativo Flask
app = Flask(__name__)

# rotas
@app.route('/')
def index():
    return "<h1>Sistema de Locação Funcionando!</h1><p>O Flask está rodando perfeitamente.</p>"

# Executa o servidor
if __name__ == '__main__':
    app.run(debug=True)