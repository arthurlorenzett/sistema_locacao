"""Cria tabela de avaliações dos espaços

Revision ID: a5b6c7d8e9f0
Revises: f4a5b6c7d8e9
Create Date: 2026-10-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a5b6c7d8e9f0'
down_revision = 'f4a5b6c7d8e9'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'avaliacoes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('reserva_id', sa.Integer(), nullable=False),
        sa.Column('espaco_id', sa.Integer(), nullable=False),
        sa.Column('locatario_id', sa.Integer(), nullable=False),
        sa.Column('nota', sa.SmallInteger(), nullable=False),
        sa.Column('comentario', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['reserva_id'], ['reservas.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['espaco_id'], ['espacos_esportivos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['locatario_id'], ['locatarios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('reserva_id'),
    )
    op.create_index('ix_avaliacoes_espaco_id', 'avaliacoes', ['espaco_id'])
    # Mesmo padrão da migration c7d8e9f0a1b2: bloqueia a API REST pública do Supabase.
    if op.get_bind().dialect.name == 'postgresql':
        op.execute('ALTER TABLE avaliacoes ENABLE ROW LEVEL SECURITY')


def downgrade():
    op.drop_index('ix_avaliacoes_espaco_id', table_name='avaliacoes')
    op.drop_table('avaliacoes')
