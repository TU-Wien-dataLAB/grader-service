"""add_submission_softdelete_column

Revision ID: a0718dae969d
Revises: 9cfeb0faa0c0
Create Date: 2024-07-06 12:12:59.091247

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a0718dae969d"
down_revision = "ba71c755c153"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "submission",
        sa.Column(
            "deleted",
            sa.Enum("active", "deleted", name="deleted"),
            server_default="active",
            nullable=False,
        ),
    )

    op.execute("UPDATE submission SET deleted = 'active'")


def downgrade():
    op.drop_column("submission", "deleted")
