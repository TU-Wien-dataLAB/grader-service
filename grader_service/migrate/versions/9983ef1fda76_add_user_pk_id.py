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

    user_table = sa.table("user", sa.column("id"), sa.column("name"))

    def _add_user_id_col(table_name: str) -> None:
        """A helper method that adds a `user_id` column and fills it based on `username`."""

        # The new column is nullable for now - until we fill it.
        op.add_column(table_name, sa.Column("user_id", sa.Integer(), nullable=True))

        table = sa.table(table_name, sa.column("username"), sa.column("user_id"))
        user_subq = (
            sa.select(user_table.c.id)
            .where(user_table.c.name == table.c.username)
            .scalar_subquery()
        )
        op.execute(table.update().values(user_id=user_subq))

        with op.batch_alter_table(table_name) as batch_op:
            batch_op.alter_column("user_id", nullable=False)

    # 2. Create a FK to user id in the "takepart" table.
    # 2.1. Create a new "user_id" column in "takepart" and fill its values based on the
    # "username" column.
    _add_user_id_col("takepart")

    # 2.2. Create FK to the user id in "takepart", update the PK, drop the "username" column.
    with op.batch_alter_table("takepart") as batch_op:
        batch_op.create_foreign_key(
            "fk_takepart_user_id",
            "user",
            ["user_id"],
            ["id"],
            # ondelete="CASCADE"  # TODO: Do we want ON DELETE CASCADE?
        )
        batch_op.create_primary_key("pk_takepart", ["user_id", "lectid"])
        batch_op.drop_column("username")

    # 3. Create a FK to user id in the "submission" table.
    # 3.1. Create a new "user_id" column in "submission" and fill its values based on the
    # username" column.
    _add_user_id_col("submission")

    # 3.2. Create FK to the user id in "submission", drop the "username" column.
    with op.batch_alter_table("submission") as batch_op:
        batch_op.create_foreign_key(
            "fk_submission_user_id",
            "user",
            ["user_id"],
            ["id"],
            # ondelete="CASCADE"  # TODO: Do we want ON DELETE CASCADE?
        )
        batch_op.drop_column("username")

    # 4. Create a FK to user id in the "api_token" table.
    # 4.1. Create a new "user_id" column in "api_token" and fill its values based on the
    # "username" column.
    _add_user_id_col("api_token")

    # 4.2. Create FK to the user id in "api_token", drop the "username" column.
    with op.batch_alter_table("api_token") as batch_op:
        batch_op.create_foreign_key(
            "fk_api_token_user_id",
            "user",
            ["user_id"],
            ["id"],
            # ondelete="CASCADE"  # TODO: Do we want ON DELETE CASCADE?
        )
        batch_op.drop_column("username")

    # 5. Create a FK to user id in the "oauth_code" table.
    # 5.1. Create a new "user_id" column in "oauth_code" and fill its values based on the
    # "username" column.
    _add_user_id_col("oauth_code")

    # 5.2. Create FK to the user id in "oauth_code", drop the "username" column.
    with op.batch_alter_table("oauth_code") as batch_op:
        batch_op.create_foreign_key(
            "fk_oauth_code_user_id",
            "user",
            ["user_id"],
            ["id"],
            # ondelete="CASCADE"  # TODO: Do we want ON DELETE CASCADE?
        )
        batch_op.drop_column("username")


def downgrade():
    user_table = sa.table("user", sa.column("id"), sa.column("name"))

    def _add_username_col(table_name: str) -> None:
        """A helper method that adds a `username` column and fills it based on `user_id`."""
        op.add_column(table_name, sa.Column("username", sa.String(length=255), nullable=True))
        table = sa.table(table_name, sa.column("username"), sa.column("user_id"))
        user_subq = (
            sa.select(user_table.c.name).where(user_table.c.id == table.c.user_id).scalar_subquery()
        )
        op.execute(table.update().values(username=user_subq))
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.alter_column("username", nullable=False)

    # # 5. Revert the change (username -> user_id) in "oauth_code".
    _add_username_col("oauth_code")

    with op.batch_alter_table("oauth_code") as batch_op:
        batch_op.create_foreign_key(
            "fk_oauth_code_username",
            "user",
            ["user_id"],
            ["id"],
            # ondelete="CASCADE"  # TODO: Do we want ON DELETE CASCADE?
        )
        batch_op.drop_column("user_id")

    # # 4. Revert the change (username -> user_id) in "api_token".
    _add_username_col("api_token")

    with op.batch_alter_table("api_token") as batch_op:
        batch_op.create_foreign_key(
            "fk_api_token_username",
            "user",
            ["user_id"],
            ["id"],
            # ondelete="CASCADE"  # TODO: Do we want ON DELETE CASCADE?
        )
        batch_op.drop_column("user_id")

    # # 3. Revert the change (username -> user_id) in "submission".
    _add_username_col("submission")

    with op.batch_alter_table("submission") as batch_op:
        batch_op.create_foreign_key(
            "fk_submission_username",
            "user",
            ["user_id"],
            ["id"],
            # ondelete="CASCADE"  # TODO: Do we want ON DELETE CASCADE?
        )
        batch_op.drop_column("user_id")

    # 2. Revert the change (username -> user_id) in "takepart".
    _add_username_col("takepart")

    with op.batch_alter_table("takepart") as batch_op:
        batch_op.create_foreign_key(
            "fk_takepart_username",
            "user",
            ["user_id"],
            ["id"],
            # ondelete="CASCADE"  # TODO: Do we want ON DELETE CASCADE?
        )
        batch_op.create_primary_key("pk_takepart", ["username", "lectid"])
        batch_op.drop_column("user_id")

    # 1. Switch back to using "name" as PK in "user".
    with op.batch_alter_table("user") as batch_op:
        batch_op.drop_column("id")
        batch_op.drop_constraint("unique_user_name")
        batch_op.create_primary_key("pk_name", columns=["name"])
