"""add reviews and rating to products

Revision ID: fedb43ee6d9d
Revises: aa3a4b166453
Create Date: 2026-03-04
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "fedb43ee6d9d"
down_revision = "aa3a4b166453"
branch_labels = None
depends_on = None


def upgrade():
    # ✅ SOMENTE adicionar colunas (não derruba tabelas!)
    op.add_column(
        "products",
        sa.Column("reviews", postgresql.JSON(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "products",
        sa.Column("rating_avg", sa.Numeric(3, 2), nullable=True),
    )
    op.add_column(
        "products",
        sa.Column("rating_count", sa.Integer(), nullable=False, server_default="0"),
    )

    # ✅ remove o default do banco (opcional, mas recomendado)
    op.alter_column("products", "rating_count", server_default=None)


def downgrade():
    # ✅ volta exatamente o que criou
    op.drop_column("products", "rating_count")
    op.drop_column("products", "rating_avg")
    op.drop_column("products", "reviews")