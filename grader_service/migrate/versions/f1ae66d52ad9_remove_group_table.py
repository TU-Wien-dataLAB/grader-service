"""remove-group-table

Revision ID: f1ae66d52ad9
Revises: 28500016a3c3
Create Date: 2025-07-14 18:45:41.948031

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f1ae66d52ad9"
down_revision = "28500016a3c3"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table("partof")
    op.drop_table("group")


def downgrade():
    op.create_table(
        "group",
        sa.Column("id", sa.Integer(), autoincrement=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("lectid", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["lectid"], ["lecture.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "partof",
        sa.Column("username", sa.String(length=255), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["group.id"]),
        sa.ForeignKeyConstraint(["username"], ["user.name"]),
        sa.PrimaryKeyConstraint("username", "group_id"),
    )
