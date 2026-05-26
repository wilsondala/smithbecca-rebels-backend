"""add status to order_items"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers
revision = "174f045ba7ac"
down_revision = "bb2e8109cd56"
branch_labels = None
depends_on = None


def table_exists(conn, table_name):
    result = conn.execute(
        text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = '{table_name}'
            );
        """)
    )
    return result.scalar()


def column_exists(conn, table_name, column_name):
    result = conn.execute(
        text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = '{table_name}'
                AND column_name = '{column_name}'
            );
        """)
    )
    return result.scalar()


def upgrade():
    conn = op.get_bind()

    # Se a tabela não existir ainda, ignora migration
    if not table_exists(conn, "order_items"):
        return

    # Se coluna já existir, ignora
    if column_exists(conn, "order_items", "status"):
        return

    op.add_column(
        "order_items",
        sa.Column("status", sa.String(length=50), nullable=True)
    )


def downgrade():
    conn = op.get_bind()

    if not table_exists(conn, "order_items"):
        return

    if not column_exists(conn, "order_items", "status"):
        return

    op.drop_column("order_items", "status")