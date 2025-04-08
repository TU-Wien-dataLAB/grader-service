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
    op.add_column('user', sa.Column('display_name',sa.Unicode(255),nullable=True))

    # set for each user the display name to the current name
    op.execute('UPDATE user SET display_name = name')

    # alter display name column of user table to not allow null values
    connection = op.get_bind()
    if connection.dialect.name != "sqlite":
        op.alter_column('user', 'display_name', nullable=False)
    else:
        with op.batch_alter_table('user') as batch_op:
            batch_op.alter_column('display_name', nullable=False)

def downgrade():
    op.drop_column('user', 'display_name')
