"""
Fábrica do Aplicativo (Application Factory).
Instancia o Flask, o banco de dados e prepara o ambiente.
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    """Cria e configura a instância do aplicativo Flask."""
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    
    from app import models  # Importa os modelos para registrar as tabelas no banco de dados
    
    from app.routes.usuario_routes import usuario_bp # Importa o Blueprint de rotas de usuário
    app.register_blueprint(usuario_bp) # Registra o Blueprint de rotas de usuário no aplicativo
    
    from app.routes.main_routes import main_bp # Importa o Blueprint de rotas principais
    app.register_blueprint(main_bp) # Registra o Blueprint de rotas principais no aplicativo

    return app