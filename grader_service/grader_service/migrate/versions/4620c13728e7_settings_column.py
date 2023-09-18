"""Settings column

Revision ID: 4620c13728e7
Revises: a1791b1371ed
Create Date: 2023-09-11 15:46:57.162396

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4620c13728e7'
down_revision = 'a1791b1371ed'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('assignment', sa.Column('settings', sa.Text, server_default='', nullable=False))


def downgrade():
    op.drop_column('assignment', 'settings')
