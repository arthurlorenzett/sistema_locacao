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

    SQLALCHEMY_TRACK_MODIFICATIONS = False