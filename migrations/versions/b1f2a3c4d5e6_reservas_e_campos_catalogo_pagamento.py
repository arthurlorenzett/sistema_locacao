"""Cria tabela de reservas e adiciona campos de catálogo, pagamento e bloqueio

Revision ID: b1f2a3c4d5e6
Revises: eecb5e240a6b
Create Date: 2026-06-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b1f2a3c4d5e6'
down_revision = 'eecb5e240a6b'
branch_labels = None
depends_on = None


def upgrade():
    # --- usuarios: bloqueio/desbloqueio ---
    op.add_column('usuarios', sa.Column('ativo', sa.Boolean(), nullable=False,
                                        server_default=sa.text('true')))

    # --- espacos_esportivos: catálogo, pagamento e ativação ---
    op.add_column('espacos_esportivos', sa.Column('regiao', sa.String(length=100), nullable=True))
    op.add_column('espacos_esportivos', sa.Column('tipo_quadra', sa.String(length=50), nullable=True))
    op.add_column('espacos_esportivos', sa.Column('descricao', sa.Text(), nullable=True))
    op.add_column('espacos_esportivos', sa.Column('endereco', sa.String(length=200), nullable=True))
    op.add_column('espacos_esportivos', sa.Column('foto_url', sa.String(length=500), nullable=True))
    op.add_column('espacos_esportivos', sa.Column('aceita_online', sa.Boolean(), nullable=False,
                                                   server_default=sa.text('true')))
    op.add_column('espacos_esportivos', sa.Column('aceita_presencial', sa.Boolean(), nullable=False,
                                                   server_default=sa.text('true')))
    op.add_column('espacos_esportivos', sa.Column('ativo', sa.Boolean(), nullable=False,
                                                   server_default=sa.text('true')))

    # --- reservas (tabela ausente na migração inicial) ---
    op.create_table(
        'reservas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('data_horario', sa.DateTime(), nullable=False),
        sa.Column('data_fim', sa.DateTime(), nullable=True),
        sa.Column('status_texto', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('metodo_pagamento', sa.String(length=20), nullable=True),
        sa.Column('status_pagamento', sa.String(length=20), nullable=True),
        sa.Column('locatario_id', sa.Integer(), nullable=False),
        sa.Column('espaco_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['locatario_id'], ['locatarios.id'], ),
        sa.ForeignKeyConstraint(['espaco_id'], ['espacos_esportivos.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('reservas')
    op.drop_column('espacos_esportivos', 'ativo')
    op.drop_column('espacos_esportivos', 'aceita_presencial')
    op.drop_column('espacos_esportivos', 'aceita_online')
    op.drop_column('espacos_esportivos', 'foto_url')
    op.drop_column('espacos_esportivos', 'endereco')
    op.drop_column('espacos_esportivos', 'descricao')
    op.drop_column('espacos_esportivos', 'tipo_quadra')
    op.drop_column('espacos_esportivos', 'regiao')
    op.drop_column('usuarios', 'ativo')
