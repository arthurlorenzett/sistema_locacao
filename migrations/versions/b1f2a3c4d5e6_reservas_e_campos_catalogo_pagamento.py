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
    # As colunas de usuários e espaços já foram adicionadas manualmente em produção, 
    # então deixamos apenas a criação da tabela de reservas.

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