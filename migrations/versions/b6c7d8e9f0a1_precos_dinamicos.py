"""Cria regras de preço por horário e grava o valor da reserva

Revision ID: b6c7d8e9f0a1
Revises: a5b6c7d8e9f0
Create Date: 2026-10-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b6c7d8e9f0a1'
down_revision = 'a5b6c7d8e9f0'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'regras_preco',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('espaco_id', sa.Integer(), nullable=False),
        sa.Column('dia_semana', sa.SmallInteger(), nullable=False),
        sa.Column('inicio', sa.SmallInteger(), nullable=False),
        sa.Column('fim', sa.SmallInteger(), nullable=False),
        sa.Column('preco_hora', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['espaco_id'], ['espacos_esportivos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_regras_preco_espaco_id', 'regras_preco', ['espaco_id'])
    # Reservas anteriores ficam sem valor gravado; a API usa o preço padrão do espaço para elas.
    op.add_column('reservas', sa.Column('valor_total', sa.Float(), nullable=True))
    # Mesmo padrão da migration c7d8e9f0a1b2: bloqueia a API REST pública do Supabase.
    if op.get_bind().dialect.name == 'postgresql':
        op.execute('ALTER TABLE regras_preco ENABLE ROW LEVEL SECURITY')


def downgrade():
    op.drop_column('reservas', 'valor_total')
    op.drop_index('ix_regras_preco_espaco_id', table_name='regras_preco')
    op.drop_table('regras_preco')
