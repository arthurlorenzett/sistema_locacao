"""Cria tabela de favoritos

Revision ID: d2e3f4a5b6c7
Revises: c7d8e9f0a1b2
Create Date: 2026-09-30 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd2e3f4a5b6c7'
down_revision = 'c7d8e9f0a1b2'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'favoritos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('locatario_id', sa.Integer(), nullable=False),
        sa.Column('espaco_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['locatario_id'], ['locatarios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['espaco_id'], ['espacos_esportivos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('locatario_id', 'espaco_id', name='uq_favorito_locatario_espaco'),
    )
    # Mesmo padrão da migration c7d8e9f0a1b2: bloqueia a API REST pública do Supabase.
    if op.get_bind().dialect.name == 'postgresql':
        op.execute('ALTER TABLE favoritos ENABLE ROW LEVEL SECURITY')


def downgrade():
    op.drop_table('favoritos')
