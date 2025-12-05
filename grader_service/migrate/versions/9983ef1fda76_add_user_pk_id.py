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
    user_table = sa.table("user", sa.column("id"), sa.column("name"))
    dialect = op.get_bind().dialect.name

    if dialect == "sqlite":
        # sqlite has to recreate the tables on `batch_alter_table`, but dropping a table
        # would cause integrity errors, so we disable the foreign key constraint temporarily
        op.execute(sa.text("PRAGMA foreign_keys=OFF"))

    # 0. Drop FKs referencing user.name
    if dialect == "postgresql":
        for table, fk in [
            ("takepart", "takepart_username_fkey"),
            ("submission", "submission_username_fkey"),
            ("api_token", "api_token_username_fkey"),
            ("oauth_code", "oauth_code_username_fkey"),
        ]:
            with op.batch_alter_table(table) as batch_op:
                batch_op.drop_constraint(fk, type_="foreignkey")

    # 1. Switch PK from name -> id
    try:
        with op.batch_alter_table("user") as batch_op:
            batch_op.drop_constraint("user_pkey", type_="primary")
    except ValueError:
        pass  # sqlite does not name PK constraints

    with op.batch_alter_table("user") as batch_op:
        if dialect == "postgresql":
            batch_op.add_column(sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True))
        elif dialect == "sqlite":
            # For sqlite, cannot add the PK constraint on column creation, because it causes
            # an IntegrityError (NOT NULL) in the temporary table.
            batch_op.add_column(sa.Column("id", sa.Integer(), nullable=False))

        batch_op.create_primary_key("pk_user_id", ["id"])
        batch_op.create_unique_constraint("unique_user_name", ["name"])

    def _add_user_id_col(table_name: str) -> None:
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

    # 2. takepart
    _add_user_id_col("takepart")
    with op.batch_alter_table("takepart") as batch_op:
        batch_op.drop_column("username")
        batch_op.create_foreign_key("fk_takepart_user_id", "user", ["user_id"], ["id"])
        batch_op.create_primary_key("pk_takepart", ["user_id", "lectid"])

    # 3. submission
    _add_user_id_col("submission")
    with op.batch_alter_table("submission") as batch_op:
        batch_op.create_foreign_key("fk_submission_user_id", "user", ["user_id"], ["id"])
        batch_op.drop_column("username")

    # 4. api_token
    _add_user_id_col("api_token")
    with op.batch_alter_table("api_token") as batch_op:
        batch_op.create_foreign_key("fk_api_token_user_id", "user", ["user_id"], ["id"])
        batch_op.drop_column("username")

    # 5. oauth_code
    _add_user_id_col("oauth_code")
    with op.batch_alter_table("oauth_code") as batch_op:
        batch_op.create_foreign_key("fk_oauth_code_user_id", "user", ["user_id"], ["id"])
        batch_op.drop_column("username")


def downgrade():
    dialect = op.get_bind().dialect.name
    if dialect == "sqlite":
        # sqlite has to recreate the tables on `batch_alter_table`, but dropping a table
        # would cause integrity errors, so we disable the foreign key constraint temporarily
        op.execute(sa.text("PRAGMA foreign_keys=OFF"))

    user_table = sa.table("user", sa.column("id"), sa.column("name"))

    def _add_username_col(table_name: str) -> None:
        """Adds a username column, fills it based on user_id, and enforces NOT NULL."""
        op.add_column(table_name, sa.Column("username", sa.String(length=255), nullable=True))

        table = sa.table(table_name, sa.column("username"), sa.column("user_id"))
        user_subq = (
            sa.select(user_table.c.name).where(user_table.c.id == table.c.user_id).scalar_subquery()
        )
        op.execute(table.update().values(username=user_subq))

    # 5. oauth_code
    _add_username_col("oauth_code")
    with op.batch_alter_table("oauth_code") as batch_op:
        batch_op.drop_constraint("fk_oauth_code_user_id", type_="foreignkey")
        batch_op.drop_column("user_id")

    # 4. api_token
    _add_username_col("api_token")
    with op.batch_alter_table("api_token") as batch_op:
        batch_op.drop_constraint("fk_api_token_user_id", type_="foreignkey")
        batch_op.drop_column("user_id")

    # 3. submission
    _add_username_col("submission")
    with op.batch_alter_table("submission") as batch_op:
        batch_op.drop_constraint("fk_submission_user_id", type_="foreignkey")
        batch_op.drop_column("user_id")

    # 2. takepart
    _add_username_col("takepart")
    with op.batch_alter_table("takepart") as batch_op:
        batch_op.drop_constraint("fk_takepart_user_id", type_="foreignkey")
        batch_op.drop_constraint("pk_takepart", type_="primary")
        batch_op.create_primary_key("pk_takepart", ["username", "lectid"])
        batch_op.drop_column("user_id")
        # Note: Only "takepart" has the constraint `nullable=False` on the "username" column (!).
        batch_op.alter_column("username", nullable=False)

    # 1. Switch PK back from id -> name
    with op.batch_alter_table("user") as batch_op:
        batch_op.drop_constraint("pk_user_id", type_="primary")
        batch_op.drop_constraint("unique_user_name", type_="unique")
        batch_op.drop_column("id")
        batch_op.create_primary_key("user_pkey", ["name"])  # restore name as PK

    # 0. Create FKs referencing user.name
    for table, fk in [
        ("takepart", "takepart_username_fkey"),
        ("submission", "submission_username_fkey"),
        ("api_token", "api_token_username_fkey"),
        ("oauth_code", "oauth_code_username_fkey"),
    ]:
        with op.batch_alter_table(table) as batch_op:
            batch_op.create_foreign_key(fk, "user", ["username"], ["name"])
