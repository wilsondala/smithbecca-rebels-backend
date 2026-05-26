"""fix render missing tables

Revision ID: 2ab7a946c879
Revises: 7ba2007c58cf
Create Date: 2026-05-22 11:55:32.584547
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2ab7a946c879"
down_revision: Union[str, None] = "7ba2007c58cf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Corrigir colunas que faltam em products no Render
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS sizes JSON")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS colors JSON")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS shoe_sizes JSON")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS video_url VARCHAR")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS rating_avg NUMERIC(3,2) DEFAULT 0")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS rating_count INTEGER DEFAULT 0")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS is_wholesale BOOLEAN DEFAULT FALSE")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS wholesale_price NUMERIC(10,2)")

    op.create_table(
    "users",
    sa.Column("id", sa.Integer(), primary_key=True, index=True),
    sa.Column("email", sa.String(), nullable=True, unique=True),
    sa.Column("name", sa.String(), nullable=True),
    sa.Column("phone", sa.String(), nullable=True),
    sa.Column("role", sa.String(), nullable=True, server_default="customer"),
    sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.text("true")),
    sa.Column("password_hash", sa.String(), nullable=True),
    sa.Column("photo", sa.String(), nullable=True),
    sa.Column("google_id", sa.String(), nullable=True),
    sa.Column("facebook_id", sa.String(), nullable=True),
    if_not_exists=True,
)

    # Criar tabela orders se não existir
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("status", sa.String(), nullable=True, server_default="pending"),
        sa.Column("payment_status", sa.String(), nullable=True, server_default="pending"),
        sa.Column("payment_method", sa.String(), nullable=True),
        sa.Column("payment_reference", sa.String(), nullable=True),
        sa.Column("delivery_fee", sa.Numeric(10, 2), nullable=True, server_default="0"),
        sa.Column("delivery_address", sa.String(), nullable=True),
        sa.Column("customer_name", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("address_line", sa.String(), nullable=True),
        sa.Column("neighborhood", sa.String(), nullable=True),
        sa.Column("reference", sa.String(), nullable=True),
        sa.Column("latitude", sa.String(), nullable=True),
        sa.Column("longitude", sa.String(), nullable=True),
        sa.Column("total", sa.Numeric(10, 2), nullable=True, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        if_not_exists=True,
    )

    # Criar tabela order_items se não existir
    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=True),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=True, server_default="1"),
        sa.Column("price", sa.Numeric(10, 2), nullable=True, server_default="0"),
        sa.Column("status", sa.String(), nullable=True, server_default="pending"),
        if_not_exists=True,
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS order_items")
    op.execute("DROP TABLE IF EXISTS orders")