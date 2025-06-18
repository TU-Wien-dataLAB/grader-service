"""add user display name

Revision ID: 28500016a3c3
Revises: fc5d2febe781
Create Date: 2025-04-08 12:10:09.318559

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "28500016a3c3"
down_revision = "fc5d2febe781"
branch_labels = None
depends_on = None


def upgrade():
    # Step 1: Add column as nullable
    op.add_column("user", sa.Column("display_name", sa.String(), nullable=True))

    # Step 2: Copy data from 'name' to 'display_name'
    user_table = sa.table(
        "user", sa.column("name", sa.String), sa.column("display_name", sa.String)
    )
    op.execute(user_table.update().values(display_name=user_table.c.name))

    # Step 3: Make the column non-nullable
    # SQLite needs batch mode; PostgreSQL can handle direct alter
    with op.batch_alter_table("user") as batch_op:
        batch_op.alter_column("display_name", nullable=False)


def downgrade():
    op.drop_column("user", "display_name")
