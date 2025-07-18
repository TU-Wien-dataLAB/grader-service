"""add user PK id

Revision ID: 9983ef1fda76
Revises: f1ae66d52ad9
Create Date: 2025-07-16 18:36:33.564133

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "9983ef1fda76"
down_revision = "597857864aed"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create user id column, make it the primary key.
    with op.batch_alter_table("user") as batch_op:
        batch_op.add_column(sa.Column("id", sa.Integer(), nullable=False))
        batch_op.create_primary_key("pk_user_id", columns=["id"])
        batch_op.create_unique_constraint("unique_user_name", ["name"])

    # 2. Create a FK to user id in "takepart".
    # 2.1. Create a new "user_id" column in "takepart"; it is nullable for now, until we fill it.
    op.add_column("takepart", sa.Column("user_id", sa.Integer(), nullable=True))

    # 2.2. Set the user_id values to the correct ids from the user table.
    # TODO: Can it be done with sqlalchemy?
    op.execute(
        """
            UPDATE takepart
            SET user_id = (
                SELECT id FROM user WHERE user.name = takepart.username
            );
            """
    )

    # 2.3. Create FK to the user id in takepart, update the PK, drop the reference to username.
    with op.batch_alter_table("takepart") as batch_op:
        # TODO: Do we want ON DELETE CASCADE?
        batch_op.create_foreign_key(
            "fk_takepart_user_id",
            "user",
            ["user_id"],
            ["id"],
            # ondelete="CASCADE"
        )
        batch_op.alter_column("user_id", nullable=False)
        batch_op.create_primary_key("pk_takepart", ["user_id", "lectid"])
        batch_op.drop_column("username")

    # 3. Create a FK to user id in "submission".
    # 3.1. Create a new "user_id" column in "submission"; it is nullable for now, until we fill it.
    op.add_column("submission", sa.Column("user_id", sa.Integer(), nullable=True))

    # 3.2. Set the user_id values to the correct ids from the user table.
    # TODO: Can it be done with sqlalchemy?
    op.execute(
        """
        UPDATE submission
        SET user_id = (SELECT id
                       FROM user
                       WHERE user.name = submission.username);
        """
    )

    # 3.3. Create FK to the user id in submission, drop the reference to username.
    with op.batch_alter_table("submission") as batch_op:
        # TODO: Do we want ON DELETE CASCADE?
        batch_op.create_foreign_key(
            "fk_submission_user_id",
            "user",
            ["user_id"],
            ["id"],
            # ondelete="CASCADE"
        )
        batch_op.alter_column("user_id", nullable=False)
        batch_op.drop_column("username")


def downgrade():
    # # 3. Revert the change (username -> user_id) in "submission".
    op.add_column("submission", sa.Column("username", sa.String(length=255), nullable=True))
    # TODO: Can it be done with sqlalchemy?
    op.execute(
        """
            UPDATE submission
            SET username = (
                SELECT name FROM user WHERE user.id = submission.user_id
            );
            """
    )
    with op.batch_alter_table("submission") as batch_op:
        # TODO: Do we want ON DELETE CASCADE?
        batch_op.create_foreign_key(
            "fk_submission_username",
            "user",
            ["user_id"],
            ["id"],
            # ondelete="CASCADE"
        )
        batch_op.alter_column("username", nullable=False)
        batch_op.drop_column("user_id")

    # 2. Revert the change (username -> user_id) in "takepart".
    op.add_column("takepart", sa.Column("username", sa.String(length=255), nullable=True))
    # TODO: Can it be done with sqlalchemy?
    op.execute(
        """
            UPDATE takepart
            SET username = (
                SELECT name FROM user WHERE user.id = takepart.user_id
            );
            """
    )
    with op.batch_alter_table("takepart") as batch_op:
        # TODO: Do we want ON DELETE CASCADE?
        batch_op.create_foreign_key(
            "fk_takepart_username",
            "user",
            ["user_id"],
            ["id"],
            # ondelete="CASCADE"
        )
        batch_op.alter_column("username", nullable=False)
        batch_op.create_primary_key("pk_takepart", ["username", "lectid"])
        batch_op.drop_column("user_id")

    # 1. Switch back to using "name" as PK in "user".
    with op.batch_alter_table("user") as batch_op:
        batch_op.drop_column("id")
        batch_op.drop_constraint("unique_user_name")
        batch_op.create_primary_key("pk_name", columns=["name"])
