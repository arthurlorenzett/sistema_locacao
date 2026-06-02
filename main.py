from flask import Flask

# Inicializa o aplicativo Flask
app = Flask(__name__)

# rotas
@app.route('/')
def index():
    return "<h1>Hello, World!</h1>"

# Executa o servidor
if __name__ == '__main__':
    app.run(debug=True)