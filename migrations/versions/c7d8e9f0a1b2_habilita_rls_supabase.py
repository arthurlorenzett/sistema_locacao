"""Habilita Row Level Security nas tabelas (bloqueia acesso pela API REST do Supabase)

O Supabase expõe o schema `public` via API REST para quem tiver a chave pública
(anon/publishable). Com RLS ligado e nenhuma policy, esse acesso fica bloqueado;
o backend Flask conecta como dono das tabelas e não é afetado.

Revision ID: c7d8e9f0a1b2
Revises: b1f2a3c4d5e6
Create Date: 2026-09-30 00:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'c7d8e9f0a1b2'
down_revision = 'b1f2a3c4d5e6'
branch_labels = None
depends_on = None

_TABELAS = ('usuarios', 'administradores', 'locadores', 'locatarios',
            'espacos_esportivos', 'reservas', 'alembic_version')


def upgrade():
    if op.get_bind().dialect.name != 'postgresql':
        return
    for tabela in _TABELAS:
        op.execute(f'ALTER TABLE {tabela} ENABLE ROW LEVEL SECURITY')


def downgrade():
    if op.get_bind().dialect.name != 'postgresql':
        return
    for tabela in _TABELAS:
        op.execute(f'ALTER TABLE {tabela} DISABLE ROW LEVEL SECURITY')
