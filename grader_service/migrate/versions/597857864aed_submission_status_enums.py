"""Use defined enums as values of submission's statuses

Revision ID: 597857864aed
Revises: f1ae66d52ad9
Create Date: 2025-08-05 17:39:45.007718

"""

import sqlalchemy as sa
from alembic import op

from grader_service.orm.submission import AutoStatus, ManualStatus

# revision identifiers, used by Alembic.
revision = "597857864aed"
down_revision = "f1ae66d52ad9"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("submission", schema=None) as batch_op:
        batch_op.alter_column("auto_status", type=AutoStatus)
        batch_op.execute("UPDATE submission SET auto_status = UPPER(auto_status);")
        batch_op.alter_column("manual_status", type=ManualStatus)
        batch_op.execute("UPDATE submission SET manual_status = UPPER(manual_status);")
        batch_op.alter_column("feedback_status", type=ManualStatus)
        batch_op.execute("UPDATE submission SET feedback_status = UPPER(feedback_status);")


def downgrade():
    with op.batch_alter_table("submission", schema=None) as batch_op:
        feedback_enum = sa.Enum(
            "not_generated",
            "generated",
            "generating",
            "generation_failed",
            "feedback_outdated",
            name="feedback_status",
        )
        batch_op.alter_column("feedback_status", type=feedback_enum)
        batch_op.execute("UPDATE submission SET feedback_status = LOWER(feedback_status);")

        manual_enum = sa.Enum("not_graded", "manually_graded", "being_edited", name="manual_status")
        batch_op.alter_column("manual_status", type=manual_enum)
        batch_op.execute("UPDATE submission SET manual_status = LOWER(manual_status);")

        auto_enum = sa.Enum(
            "pending", "not_graded", "automatically_graded", "grading_failed", name="auto_status"
        )
        batch_op.alter_column("auto_status", type=auto_enum)
        batch_op.execute("UPDATE submission SET auto_status = LOWER(auto_status);")
