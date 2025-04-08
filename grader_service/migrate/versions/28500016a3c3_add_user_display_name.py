"""add user display name

Revision ID: 28500016a3c3
Revises: fc5d2febe781
Create Date: 2025-04-08 12:10:09.318559

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '28500016a3c3'
down_revision = 'fc5d2febe781'
branch_labels = None
depends_on = None


def upgrade():
    # add display name column to user table without data
    op.add_column('user', sa.Column('display_name', sa.Unicode(255), nullable=False, server_default=sa.Computed('name')))

def downgrade():
    op.drop_column('user', 'display_name')
