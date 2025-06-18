"""merged assignment configuration options into assignment settings column

Revision ID: fc5d2febe781
Revises: a0718dae969d
Create Date: 2025-01-27 15:42:24.363658

"""

import datetime
import json

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "fc5d2febe781"
down_revision = "a0718dae969d"
branch_labels = None
depends_on = None


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


def upgrade():
    # Migrate data from old columns to the settings column
    conn = op.get_bind()
    assignments = conn.execute(
        sa.text(
            "SELECT id, duedate, type, automatic_grading, max_submissions, allow_files, settings FROM assignment"
        )
    )

    for assignment in assignments:
        assignment = dict(zip(assignments.keys(), assignment))
        existing_settings = json.loads(assignment["settings"]) if assignment["settings"] else {}
        new_settings = {
            "deadline": assignment["duedate"] if assignment["duedate"] else None,
            "assignment_type": assignment["type"],
            "autograde_type": assignment["automatic_grading"],
            "max_submissions": assignment["max_submissions"],
            "allowed_files": ["*"] if bool(assignment["allow_files"]) else [],
        }
        existing_settings.update(new_settings)
        conn.execute(
            sa.text("UPDATE assignment SET settings = :settings WHERE id = :id"),
            {
                "settings": json.dumps(existing_settings, default=json_serial),
                "id": assignment["id"],
            },
        )

    # Drop the old columns
    op.drop_column("assignment", "duedate")
    op.drop_column("assignment", "type")
    op.drop_column("assignment", "automatic_grading")
    op.drop_column("assignment", "max_submissions")
    op.drop_column("assignment", "allow_files")


def downgrade():
    # Recreate the old columns
    # Drop the old columns
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col["name"] for col in inspector.get_columns("assignment")]
    if "duedate" not in columns:
        op.add_column("assignment", sa.Column("duedate", sa.DateTime(), nullable=True))
    if "type" not in columns:
        op.add_column(
            "assignment",
            sa.Column(
                "type",
                sa.Enum("user", "group", name="assignment_type"),
                nullable=False,
                server_default="user",
            ),
        )
    if "automatic_grading" not in columns:
        op.add_column(
            "assignment",
            sa.Column(
                "automatic_grading",
                sa.Enum("unassisted", "auto", "full_auto", name="automatic_grading"),
                server_default="auto",
                nullable=False,
            ),
        )
    if "max_submissions" not in columns:
        op.add_column(
            "assignment",
            sa.Column(
                "max_submissions", sa.Integer(), nullable=True, server_default=None, unique=False
            ),
        )
    if "allow_files" not in columns:
        op.add_column(
            "assignment",
            sa.Column(
                "allow_files", sa.Boolean(), nullable=False, server_default="f", default=False
            ),
        )

    # Migrate data back from the settings column to the old columns
    assignments = conn.execute(sa.text("SELECT id, settings FROM assignment"))

    for assignment in assignments:
        assignment = dict(zip(assignments.keys(), assignment))
        settings = json.loads(assignment["settings"]) if assignment["settings"] else {}
        conn.execute(
            sa.text(
                """
                UPDATE assignment
                SET duedate = :duedate, type = :type, automatic_grading = :automatic_grading,
                    max_submissions = :max_submissions, allow_files = :allow_files
                WHERE id = :id
                """
            ),
            {
                "duedate": datetime.datetime.fromisoformat(settings["deadline"])
                if settings.get("deadline")
                else None,
                "type": settings.get("assignment_type"),
                "automatic_grading": settings.get("autograde_type"),
                "max_submissions": settings.get("max_submissions"),
                "allow_files": len(settings.get("allowed_files")) > 0,
                "id": assignment["id"],
            },
        )
