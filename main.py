"""
Ponto de entrada principal da aplicação.
Importa a fábrica do aplicativo Flask e inicia o servidor de desenvolvimento.

Em produção (Render) o servidor é iniciado com: gunicorn main:app
"""

import os

from flask_migrate import upgrade, stamp
from sqlalchemy import inspect
from sqlalchemy.exc import OperationalError

from app import create_app, db

_DIR_MIGRATIONS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'migrations')


def preparar_banco():
    """Deixa o schema do banco em dia aplicando as migrations (Alembic).

    Bancos criados por versões antigas via `db.create_all()` não têm a tabela
    `alembic_version`; nesse caso as tabelas faltantes são criadas e o banco é
    marcado como atualizado, para que as próximas migrations funcionem.
    """
    tabelas = inspect(db.engine).get_table_names()
    if 'usuarios' in tabelas and 'alembic_version' not in tabelas:
        db.create_all()
        stamp(directory=_DIR_MIGRATIONS)
    else:
        upgrade(directory=_DIR_MIGRATIONS)


# Cria a instância do aplicativo configurado
app = create_app()

with app.app_context():
    try:
        preparar_banco()
    except OperationalError as e:
        # Mensagem curta no log do Render em vez de um traceback de 200 linhas.
        raise SystemExit(
            "ERRO: não foi possível conectar ao banco de dados definido em DATABASE_URL.\n"
            "Verifique se o banco existe/está ativo (projetos Supabase free são pausados "
            "por inatividade) e se a URL está correta.\n"
            f"Detalhe: {e.orig}"
        ) from None

if __name__ == '__main__':
    # Roda o servidor na porta 5000 com o modo de depuração (debug) ativado
    app.run(debug=True)
