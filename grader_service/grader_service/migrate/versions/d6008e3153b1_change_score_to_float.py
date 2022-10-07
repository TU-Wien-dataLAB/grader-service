"""Change score to float

Revision ID: d6008e3153b1
Revises: a1791b1371ed
Create Date: 2022-10-07 09:41:36.776282

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd6008e3153b1'
down_revision = 'a1791b1371ed'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('assignment', schema=None) as batch_op:
        batch_op.alter_column("points",
                              nullable=False,
                              type_=sa.DECIMAL(10, 3),
                              existing_nullable=False,
                              existing_type=sa.Integer())
    with op.batch_alter_table('submission', schema=None) as batch_op:
        batch_op.alter_column("score",
                              nullable=True,
                              type_=sa.DECIMAL(10, 3),
                              existing_nullable=True,
                              existing_type=sa.Integer())


def downgrade():
    with op.batch_alter_table('assignment', schema=None) as batch_op:
        batch_op.alter_column("points",
                              nullable=False,
                              type_=sa.Integer(),
                              existing_nullable=False,
                              existing_type=sa.DECIMAL(10, 3))
    with op.batch_alter_table('submission', schema=None) as batch_op:
        batch_op.alter_column("score",
                              nullable=True,
                              type_=sa.Integer(),
                              existing_nullable=True,
                              existing_type=sa.DECIMAL(10, 3))
