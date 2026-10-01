"""Cria tabela de bloqueios manuais de agenda

Revision ID: f4a5b6c7d8e9
Revises: e3f4a5b6c7d8
Create Date: 2026-09-30 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f4a5b6c7d8e9'
down_revision = 'e3f4a5b6c7d8'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'bloqueios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('espaco_id', sa.Integer(), nullable=False),
        sa.Column('inicio', sa.DateTime(), nullable=False),
        sa.Column('fim', sa.DateTime(), nullable=False),
        sa.Column('motivo', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['espaco_id'], ['espacos_esportivos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_bloqueios_espaco_id', 'bloqueios', ['espaco_id'])
    # Mesmo padrão da migration c7d8e9f0a1b2: bloqueia a API REST pública do Supabase.
    if op.get_bind().dialect.name == 'postgresql':
        op.execute('ALTER TABLE bloqueios ENABLE ROW LEVEL SECURITY')


def downgrade():
    op.drop_index('ix_bloqueios_espaco_id', table_name='bloqueios')
    op.drop_table('bloqueios')
