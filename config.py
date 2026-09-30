"""
Módulo de configuração da aplicação Flask.
Gerencia as variáveis de ambiente e as configurações do banco de dados.
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """
    Classe base de configuração.
    
    Atributos:
        SQLALCHEMY_DATABASE_URI (str): URL de conexão com o banco de dados PostgreSQL.
        SQLALCHEMY_TRACK_MODIFICATIONS (bool): Desativa o rastreamento de modificações do SQLAlchemy para economizar memória.
    """
    
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')

    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("A variável DATABASE_URL não foi encontrada. Verifique seu arquivo .env!")

    # Alguns provedores (Heroku, Render antigo) entregam 'postgres://', que o SQLAlchemy 2 não aceita.
    if SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Em produção o banco é remoto (Supabase/Render) e derruba conexões ociosas;
    # pre_ping descarta conexões mortas em vez de devolver erro 500 ao usuário.
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 280,
    }

    # Chave usada para assinar os tokens de autenticação (itsdangerous).
    # Em produção deve vir do ambiente; o fallback serve apenas para dev local.
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-arena-facil-troque-em-producao')