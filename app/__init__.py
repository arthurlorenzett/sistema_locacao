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

    return app