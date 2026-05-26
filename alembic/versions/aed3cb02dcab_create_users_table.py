"""create users table

Revision ID: aed3cb02dcab
Revises: bf1d6c3329cd
Create Date: 2026-02-02 02:14:56.463404

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'aed3cb02dcab'
down_revision: Union[str, None] = 'bf1d6c3329cd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('email', sa.String, nullable=False, unique=True),
        sa.Column('password_hash', sa.String, nullable=False),
        sa.Column('phone', sa.String),
        sa.Column('role', sa.String, default='client'),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime),
    )
    op.create_index('ix_users_id', 'users', ['id'])

def downgrade():
    op.drop_index('ix_users_id', table_name='users')
    op.drop_table('users')
