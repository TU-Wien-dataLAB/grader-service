"""Use defined enums as values of submission's statuses

Revision ID: 597857864aed
Revises: f1ae66d52ad9
Create Date: 2025-08-05 17:39:45.007718

"""

from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "597857864aed"
down_revision = "f1ae66d52ad9"
branch_labels = None
depends_on = None


# Enum values
AUTO_STATUS_OLD = ["not_graded", "pending", "automatically_graded", "grading_failed"]
AUTO_STATUS_NEW = [v.upper() for v in AUTO_STATUS_OLD]

MANUAL_STATUS_OLD = ["not_graded", "manually_graded", "being_edited"]
MANUAL_STATUS_NEW = [v.upper() for v in MANUAL_STATUS_OLD]

FEEDBACK_STATUS_OLD = [
    "not_generated",
    "generating",
    "generated",
    "generation_failed",
    "feedback_outdated",
]
FEEDBACK_STATUS_NEW = [v.upper() for v in FEEDBACK_STATUS_OLD]


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        # PostgreSQL: create new enums and swap
        _upgrade_postgresql(bind)
    else:
        # SQLite (or others): just update text
        _upgrade_sqlite()


def downgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        _downgrade_postgresql(bind)
    else:
        _downgrade_sqlite()


# ----------------------
# PostgreSQL helpers
# ----------------------
def _upgrade_postgresql(bind):
    # AUTO_STATUS
    auto_status_new = postgresql.ENUM(*AUTO_STATUS_NEW, name="auto_status_new")
    auto_status_new.create(bind, checkfirst=False)
    op.alter_column(
        "submission",
        "auto_status",
        type_=auto_status_new,
        postgresql_using="UPPER(auto_status::text)::auto_status_new",
    )
    op.execute("DROP TYPE auto_status")
    op.execute("ALTER TYPE auto_status_new RENAME TO auto_status")

    # MANUAL_STATUS
    manual_status_new = postgresql.ENUM(*MANUAL_STATUS_NEW, name="manual_status_new")
    manual_status_new.create(bind, checkfirst=False)
    op.alter_column(
        "submission",
        "manual_status",
        type_=manual_status_new,
        postgresql_using="UPPER(manual_status::text)::manual_status_new",
    )
    op.execute("DROP TYPE manual_status")
    op.execute("ALTER TYPE manual_status_new RENAME TO manual_status")

    # FEEDBACK_STATUS
    feedback_status_new = postgresql.ENUM(*FEEDBACK_STATUS_NEW, name="feedback_status_new")
    feedback_status_new.create(bind, checkfirst=False)

    # Drop default first
    op.execute("ALTER TABLE submission ALTER COLUMN feedback_status DROP DEFAULT")

    op.alter_column(
        "submission",
        "feedback_status",
        type_=feedback_status_new,
        postgresql_using="UPPER(feedback_status::text)::feedback_status_new",
    )
    op.execute("DROP TYPE feedback_status")
    op.execute("ALTER TYPE feedback_status_new RENAME TO feedback_status")


def _downgrade_postgresql(bind):
    auto_status_old = postgresql.ENUM(*AUTO_STATUS_OLD, name="auto_status_old")
    auto_status_old.create(bind, checkfirst=False)
    op.alter_column(
        "submission",
        "auto_status",
        type_=auto_status_old,
        postgresql_using="LOWER(auto_status::text)::auto_status_old",
    )
    op.execute("DROP TYPE auto_status")
    op.execute("ALTER TYPE auto_status_old RENAME TO auto_status")

    manual_status_old = postgresql.ENUM(*MANUAL_STATUS_OLD, name="manual_status_old")
    manual_status_old.create(bind, checkfirst=False)
    op.alter_column(
        "submission",
        "manual_status",
        type_=manual_status_old,
        postgresql_using="LOWER(manual_status::text)::manual_status_old",
    )
    op.execute("DROP TYPE manual_status")
    op.execute("ALTER TYPE manual_status_old RENAME TO manual_status")

    feedback_status_old = postgresql.ENUM(*FEEDBACK_STATUS_OLD, name="feedback_status_old")
    feedback_status_old.create(bind, checkfirst=False)
    op.alter_column(
        "submission",
        "feedback_status",
        type_=feedback_status_old,
        postgresql_using="LOWER(feedback_status::text)::feedback_status_old",
    )
    op.execute("DROP TYPE feedback_status")
    op.execute("ALTER TYPE feedback_status_old RENAME TO feedback_status")
    # restore default
    op.execute("ALTER TABLE submission ALTER COLUMN feedback_status SET DEFAULT 'not_generated'")


# ----------------------
# SQLite helpers
# ----------------------
def _upgrade_sqlite():
    op.execute("UPDATE submission SET auto_status = UPPER(auto_status)")
    op.execute("UPDATE submission SET manual_status = UPPER(manual_status)")
    op.execute("UPDATE submission SET feedback_status = UPPER(feedback_status)")


def _downgrade_sqlite():
    op.execute("UPDATE submission SET auto_status = LOWER(auto_status)")
    op.execute("UPDATE submission SET manual_status = LOWER(manual_status)")
    op.execute("UPDATE submission SET feedback_status = LOWER(feedback_status)")
