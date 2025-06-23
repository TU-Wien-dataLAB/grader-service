"""Add feedback status

Revision ID: 9cfeb0faa0c0
Revises: 4620c13728e7
Create Date: 2024-01-10 15:16:36.273796

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "9cfeb0faa0c0"
down_revision = "4620c13728e7"
branch_labels = None
depends_on = None


def upgrade():
    sa_enum = sa.Enum(
        "not_generated",
        "generated",
        "generating",
        "generation_failed",
        "feedback_outdated",
        name="feedback_status",
    )
    # This will create the enum if it's not already present
    sa_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "submission",
        sa.Column("feedback_status", sa_enum, server_default="not_generated", nullable=False),
    )

    op.execute(
        "UPDATE submission SET feedback_status='not_generated' WHERE feedback_available=false"
    )
    op.execute("UPDATE submission SET feedback_status='generated' WHERE feedback_available=true")
    op.drop_column("submission", "feedback_available")


def downgrade():
    op.add_column(
        "submission",
        sa.Column("feedback_available", sa.Boolean, server_default="false", nullable=False),
    )
    op.execute(
        "UPDATE submission SET feedback_available=false WHERE feedback_status='not_generated' OR feedback_status='generation_failed' OR feedback_status='generating'"
    )
    op.execute(
        "UPDATE submission SET feedback_available=true WHERE feedback_status='generated' OR feedback_status='feedback_outdated'"
    )
    op.drop_column("submission", "feedback_status")

    sa_enum = sa.Enum(name="feedback_status")
    sa_enum.drop(op.get_bind(), checkfirst=True)
