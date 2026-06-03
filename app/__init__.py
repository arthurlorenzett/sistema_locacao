"""
Módulo de inicialização da aplicação (Application Factory).
Configura o Flask, o banco de dados e registra os Blueprints de rotas.
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

# Inicialização das extensões do Flask
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    """
    Fábrica de Criação do Aplicativo.
    Instancia o Flask, aplica as configurações e acopla as rotas.
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    # Conecta o banco de dados e o sistema de migração ao app
    db.init_app(app)
    migrate.init_app(app, db)

    # Importa e registra o Blueprint da nossa rota de teste
    from app.routes.base_routes import base_bp
    app.register_blueprint(base_bp)

    return app