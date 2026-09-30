"""Cria tabela de horários de funcionamento dos espaços

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
Create Date: 2026-09-30 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e3f4a5b6c7d8'
down_revision = 'd2e3f4a5b6c7'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'horarios_funcionamento',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('espaco_id', sa.Integer(), nullable=False),
        sa.Column('dia_semana', sa.SmallInteger(), nullable=False),
        sa.Column('abertura', sa.SmallInteger(), nullable=False),
        sa.Column('fechamento', sa.SmallInteger(), nullable=False),
        sa.ForeignKeyConstraint(['espaco_id'], ['espacos_esportivos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('espaco_id', 'dia_semana', name='uq_horario_espaco_dia'),
    )
    # Mesmo padrão da migration c7d8e9f0a1b2: bloqueia a API REST pública do Supabase.
    if op.get_bind().dialect.name == 'postgresql':
        op.execute('ALTER TABLE horarios_funcionamento ENABLE ROW LEVEL SECURITY')


def downgrade():
    op.drop_table('horarios_funcionamento')
