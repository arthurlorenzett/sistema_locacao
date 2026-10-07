"""Liga as reservas recorrentes (mensalista) por um id de série

Revision ID: c7d8e9f0a1b3
Revises: b6c7d8e9f0a1
Create Date: 2026-10-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c7d8e9f0a1b3'
down_revision = 'b6c7d8e9f0a1'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('reservas', sa.Column('serie_id', sa.String(length=36), nullable=True))
    op.create_index('ix_reservas_serie_id', 'reservas', ['serie_id'])


def downgrade():
    op.drop_index('ix_reservas_serie_id', table_name='reservas')
    op.drop_column('reservas', 'serie_id')
