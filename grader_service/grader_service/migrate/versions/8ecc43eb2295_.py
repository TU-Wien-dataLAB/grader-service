"""Add edited column to submission

Revision ID: 8ecc43eb2295
Revises: d6008e3153b1
Create Date: 2023-02-01 13:39:46.912838

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8ecc43eb2295'
down_revision = 'd6008e3153b1'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('submission',sa.Column('edited', sa.Boolean, default=False))


def downgrade():
    with op.batch_alter_table('submission', schema=None) as batch_op:
        batch_op.drop_column("edited")
