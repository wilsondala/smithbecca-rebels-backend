"""add variations to products

Revision ID: add_variations_to_products
Revises: <COLOQUE_A_REVISAO_ANTERIOR_AQUI>
Create Date: 2026-03-25
"""

from alembic import op
import sqlalchemy as sa


# revise estes IDs
revision = "20260325_add_variations"
down_revision = "1497e41fe609"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("products", sa.Column("variations", sa.JSON(), nullable=True))


def downgrade():
    op.drop_column("products", "variations")