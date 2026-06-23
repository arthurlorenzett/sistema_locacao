"""
Fábrica do Aplicativo (Application Factory).
Instancia o Flask, o banco de dados e prepara o ambiente.
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

# Instancia as extensões globalmente (mas sem vinculá-las a um app específico ainda)
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    """Cria e configura a instância do aplicativo Flask."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Vincula o app atual às extensões
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Importa os modelos para que o Alembic consiga "ler" as classes 
    # e registrar as tabelas no banco de dados
    from app import models 
    
    # Importa os Blueprints
    from app.routes.usuario_routes import usuario_bp
    from app.routes.reserva_routes import reserva_bp
    from app.routes.espaco_routes import espaco_bp

    # (Opcional) Importa o main_bp se você for criar uma rota raiz ('/')
    from app.routes.main_routes import main_bp
    app.register_blueprint(main_bp)

    # Registra os Blueprints no sistema, definindo prefixos claros nas URLs
    app.register_blueprint(usuario_bp, url_prefix='/usuarios')
    app.register_blueprint(reserva_bp, url_prefix='/reservas')
    app.register_blueprint(espaco_bp, url_prefix='/espacos')

    _registrar_handlers_erro(app)

    return app


def _registrar_handlers_erro(app):
    """Garante respostas JSON (nunca HTML/stacktrace) para erros comuns."""
    from flask import jsonify

    @app.errorhandler(404)
    def _nao_encontrado(_e):
        return jsonify({"erro": "Recurso não encontrado."}), 404

    @app.errorhandler(405)
    def _metodo_invalido(_e):
        return jsonify({"erro": "Método não permitido."}), 405

    @app.errorhandler(500)
    def _erro_interno(_e):
        db.session.rollback()
        return jsonify({"erro": "Erro interno no servidor."}), 500