from alembic import op
import sqlalchemy as sa

revision = 'NOVO_ID'
down_revision = 'afbc1f54e08e'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'products',
        sa.Column('category', sa.String(), nullable=True)
    )
    op.create_index('ix_products_category', 'products', ['category'], unique=False)


def downgrade():
    op.drop_index('ix_products_category', table_name='products')
    op.drop_column('products', 'category')