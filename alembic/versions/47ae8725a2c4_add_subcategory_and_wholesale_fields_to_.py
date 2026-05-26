"""add subcategory and wholesale fields to products

Revision ID: 47ae8725a2c4
Revises: NOVO_ID
Create Date: 2026-02-28 14:48:45.264258
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "47ae8725a2c4"
down_revision: Union[str, None] = "NOVO_ID"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =========================
    # Subcategory
    # =========================
    op.add_column("products", sa.Column("subcategory", sa.String(), nullable=True))
    op.create_index("ix_products_subcategory", "products", ["subcategory"], unique=False)

    # =========================
    # Wholesale
    # =========================
    op.add_column(
        "products",
        sa.Column(
            "is_wholesale",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column("products", sa.Column("wholesale_price", sa.Numeric(10, 2), nullable=True))

    # =========================
    # Kit
    # =========================
    op.add_column(
        "products",
        sa.Column(
            "is_kit",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )



def downgrade() -> None:
    op.drop_column("products", "is_kit")
    op.drop_column("products", "wholesale_price")
    op.drop_column("products", "is_wholesale")

    op.drop_index("ix_products_subcategory", table_name="products")
    op.drop_column("products", "subcategory")