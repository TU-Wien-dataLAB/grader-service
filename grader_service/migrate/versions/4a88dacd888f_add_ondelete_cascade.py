"""add ondelete cascade

Revision ID: 4a88dacd888f
Revises: 9983ef1fda76
Create Date: 2025-11-04 11:55:10.513853

"""

from typing import Dict, List

from alembic import op
from sqlalchemy import (
    Column,
    Connection,
    Inspector,
    MetaData,
    String,
    Table,
    and_,
    inspect,
    select,
    text,
)

# revision identifiers, used by Alembic.
revision = "4a88dacd888f"
down_revision = "9983ef1fda76"
branch_labels = None
depends_on = None


"""
- Standardizes the names of all foreign keys regardless of the database used.
    - SQLite: None -> fk_<table>_<local_col>
    - PostgreSQL: <table>_<local_col>_fkey -> fk_<table>_<local_col>
- Adds the new foreign key “fk_api_token_client_id”.
- Due to the new foreign key “fk_api_token_client_id,” invalid “api_token” entries are deleted.
- All foreign keys receive the option ondelete="CASCADE".
- The new table “alembic_fk_metadata” stores the old foreign key names so that they can be restored during downgrade.
The exception is SQLite, because SQLAlchemy does not allow “None” in names, the new foreign key names are retained.
"""


def _drop_all_foreign_keys(batch_op, connection, table_name: str):
    """
    Remove all foreign key constraints from the specified table.

    Only drops constraints that have a defined name, since unnamed foreign keys
    cannot be dropped explicitly. (SQLite)
    """
    inspector = Inspector.from_engine(connection)
    fks = inspector.get_foreign_keys(table_name)
    for fk in fks:
        if fk["name"] is not None:
            batch_op.drop_constraint(fk["name"], type_="foreignkey")


def _get_fk_name(conn, table_name, local_cols, referred_table):
    """Return the foreign key name if exists, else None (SQLite may be None)"""
    inspector = inspect(conn)
    for fk in inspector.get_foreign_keys(table_name):
        if fk["constrained_columns"] == local_cols and fk["referred_table"] == referred_table:
            return fk["name"]
    return None


def _store_old_fk(conn, table_name, local_cols, referred_table, old_name):
    """Store information about an existing foreign key in a helper table."""
    metadata = MetaData()
    fk_table = Table(
        "alembic_fk_metadata",
        metadata,
        Column("table_name", String, primary_key=True),
        Column("column_name", String, primary_key=True),
        Column("referred_table", String),
        Column("old_fk_name", String),
    )
    fk_table.create(conn, checkfirst=True)
    conn.execute(
        fk_table.insert().values(
            table_name=table_name,
            column_name=local_cols[0],
            referred_table=referred_table,
            old_fk_name=old_name,
        )
    )


def _get_stored_old_fk(conn, table_name, local_cols, referred_table):
    """Retrieve old foreign key name from a helper table"""
    metadata = MetaData()
    fk_table = Table("alembic_fk_metadata", metadata, autoload_with=conn)
    stmt = select(fk_table.c.old_fk_name).where(
        and_(
            fk_table.c.table_name == table_name,
            fk_table.c.column_name == local_cols[0],
            fk_table.c.referred_table == referred_table,
        )
    )
    result = conn.execute(stmt).first()
    return result[0] if result else None


def _upgrade_recreate_foreign_keys(
    connection: Connection, table_name: str, fk_definitions: List[Dict]
) -> None:
    """
    Recreate foreign key constraints on a table during a migration.

    Steps performed:
    1. Retrieve the current foreign key names for the given definitions.
    2. Store the old foreign key info in a helper table for reference.
    3. Drop all existing foreign key constraints on the table.
    4. Recreate the foreign keys using the new definitions with CASCADE on delete.

    :param connection: SQLAlchemy connection object.
    :type connection: sqlalchemy.engine.Connection
    :param table_name: Name of the table to alter.
    :type table_name: str
    :param fk_definitions: List of dictionaries describing foreign keys to recreate, each containing:
        - new_constraint_name: Name for the new foreign key constraint.
        - referred_table: Name of the referenced table.
        - local_cols: List of columns in the local table.
        - remote_cols: List of columns in the referenced table.
    :type fk_definitions: List[Dict]
    """
    with op.batch_alter_table(table_name) as batch_op:
        for fk in fk_definitions:
            old_name = _get_fk_name(connection, table_name, fk["local_cols"], fk["referred_table"])
            _store_old_fk(connection, table_name, fk["local_cols"], fk["referred_table"], old_name)

        _drop_all_foreign_keys(batch_op, connection, table_name)

        for fk in fk_definitions:
            batch_op.create_foreign_key(
                constraint_name=fk["new_constraint_name"],
                referent_table=fk["referred_table"],
                local_cols=fk["local_cols"],
                remote_cols=fk["remote_cols"],
                ondelete="CASCADE",
            )


def _downgrade_recreate_foreign_keys(
    connection: Connection, table_name: str, fk_definitions: List[Dict]
) -> None:
    """
    Restore previous foreign key constraints during a downgrade migration.

    For each foreign key in fk_definitions:
    1. Retrieve the old foreign key name from the helper table.
    2. Drop the new foreign key constraint (except for SQLite, which handles it differently).
    3. Recreate the old foreign key using the stored name, or fallback to the new name if none was stored.

    :param connection: SQLAlchemy connection object.
    :type connection: sqlalchemy.engine.Connection
    :param table_name: Name of the table to alter.
    :type table_name: str
    :param fk_definitions: List of dictionaries describing foreign keys to restore, each containing:
        - new_constraint_name: Name of the current foreign key constraint.
        - referred_table: Name of the referenced table.
        - local_cols: List of columns in the local table.
        - remote_cols: List of columns in the referenced table.
    :type fk_definitions: List[Dict]
    """
    with op.batch_alter_table(table_name) as batch_op:
        for fk in fk_definitions:
            old_fk_name = _get_stored_old_fk(
                connection, table_name, fk["local_cols"], fk["referred_table"]
            )
            if connection.dialect.name != "sqlite":
                batch_op.drop_constraint(fk["new_constraint_name"], type_="foreignkey")
            if old_fk_name is None:
                if connection.dialect.name != "sqlite":
                    return
                old_fk_name = fk["new_constraint_name"]
            batch_op.create_foreign_key(
                constraint_name=old_fk_name,
                referent_table=fk["referred_table"],
                local_cols=fk["local_cols"],
                remote_cols=fk["remote_cols"],
            )


def upgrade():
    connection = op.get_bind()
    dialect = op.get_bind().dialect.name

    if dialect == "sqlite":
        connection.execute(text("PRAGMA foreign_keys=OFF;"))

    _upgrade_recreate_foreign_keys(
        connection=connection,
        table_name="assignment",
        fk_definitions=[
            {
                "new_constraint_name": "fk_assignment_lectid",
                "referred_table": "lecture",
                "local_cols": ["lectid"],
                "remote_cols": ["id"],
            }
        ],
    )

    _upgrade_recreate_foreign_keys(
        connection=connection,
        table_name="submission",
        fk_definitions=[
            {
                "new_constraint_name": "fk_submission_assignid",
                "referred_table": "assignment",
                "local_cols": ["assignid"],
                "remote_cols": ["id"],
            },
            {
                "new_constraint_name": "fk_submission_user_id",
                "referred_table": "user",
                "local_cols": ["user_id"],
                "remote_cols": ["id"],
            },
        ],
    )

    _upgrade_recreate_foreign_keys(
        connection=connection,
        table_name="submission_logs",
        fk_definitions=[
            {
                "new_constraint_name": "fk_submission_logs_sub_id",
                "referred_table": "submission",
                "local_cols": ["sub_id"],
                "remote_cols": ["id"],
            }
        ],
    )

    _upgrade_recreate_foreign_keys(
        connection=connection,
        table_name="submission_properties",
        fk_definitions=[
            {
                "new_constraint_name": "fk_submission_properties_sub_id",
                "referred_table": "submission",
                "local_cols": ["sub_id"],
                "remote_cols": ["id"],
            }
        ],
    )

    _upgrade_recreate_foreign_keys(
        connection=connection,
        table_name="takepart",
        fk_definitions=[
            {
                "new_constraint_name": "fk_takepart_lectid",
                "referred_table": "lecture",
                "local_cols": ["lectid"],
                "remote_cols": ["id"],
            },
            {
                "new_constraint_name": "fk_takepart_user_id",
                "referred_table": "user",
                "local_cols": ["user_id"],
                "remote_cols": ["id"],
            },
        ],
    )

    # OAuth/LTI tokens that reference non-existent clients are deleted
    connection.execute(
        text(
            """
             DELETE
             FROM api_token
             WHERE
               client_id IS NOT NULL  -- non-OAuth tokens may not have client_id set
               AND client_id NOT IN (SELECT identifier FROM oauth_client);
             """
        )
    )
    _upgrade_recreate_foreign_keys(
        connection=connection,
        table_name="api_token",
        fk_definitions=[
            {
                "new_constraint_name": "fk_api_token_user_id",
                "referred_table": "user",
                "local_cols": ["user_id"],
                "remote_cols": ["id"],
            },
            {
                "new_constraint_name": "fk_api_token_client_id",
                "referred_table": "oauth_client",
                "local_cols": ["client_id"],
                "remote_cols": ["identifier"],
            },
        ],
    )

    _upgrade_recreate_foreign_keys(
        connection=connection,
        table_name="oauth_code",
        fk_definitions=[
            {
                "new_constraint_name": "fk_oauth_code_user_id",
                "referred_table": "user",
                "local_cols": ["user_id"],
                "remote_cols": ["id"],
            },
            {
                "new_constraint_name": "fk_oauth_code_client_id",
                "referred_table": "oauth_client",
                "local_cols": ["client_id"],
                "remote_cols": ["identifier"],
            },
        ],
    )

    if dialect == "sqlite":
        connection.execute(text("PRAGMA foreign_keys=ON;"))


def downgrade():
    connection = op.get_bind()
    dialect = op.get_bind().dialect.name

    if dialect == "sqlite":
        connection.execute(text("PRAGMA foreign_keys=OFF;"))

    _downgrade_recreate_foreign_keys(
        connection=connection,
        table_name="assignment",
        fk_definitions=[
            {
                "new_constraint_name": "fk_assignment_lectid",
                "referred_table": "lecture",
                "local_cols": ["lectid"],
                "remote_cols": ["id"],
            }
        ],
    )

    _downgrade_recreate_foreign_keys(
        connection=connection,
        table_name="submission",
        fk_definitions=[
            {
                "new_constraint_name": "fk_submission_assignid",
                "referred_table": "assignment",
                "local_cols": ["assignid"],
                "remote_cols": ["id"],
            },
            {
                "new_constraint_name": "fk_submission_user_id",
                "referred_table": "user",
                "local_cols": ["user_id"],
                "remote_cols": ["id"],
            },
        ],
    )

    _downgrade_recreate_foreign_keys(
        connection=connection,
        table_name="submission_logs",
        fk_definitions=[
            {
                "new_constraint_name": "fk_submission_logs_sub_id",
                "referred_table": "submission",
                "local_cols": ["sub_id"],
                "remote_cols": ["id"],
            }
        ],
    )

    _downgrade_recreate_foreign_keys(
        connection=connection,
        table_name="submission_properties",
        fk_definitions=[
            {
                "new_constraint_name": "fk_submission_properties_sub_id",
                "referred_table": "submission",
                "local_cols": ["sub_id"],
                "remote_cols": ["id"],
            }
        ],
    )

    _downgrade_recreate_foreign_keys(
        connection=connection,
        table_name="takepart",
        fk_definitions=[
            {
                "new_constraint_name": "fk_takepart_lectid",
                "referred_table": "lecture",
                "local_cols": ["lectid"],
                "remote_cols": ["id"],
            },
            {
                "new_constraint_name": "fk_takepart_user_id",
                "referred_table": "user",
                "local_cols": ["user_id"],
                "remote_cols": ["id"],
            },
        ],
    )

    _downgrade_recreate_foreign_keys(
        connection=connection,
        table_name="api_token",
        fk_definitions=[
            {
                "new_constraint_name": "fk_api_token_user_id",
                "referred_table": "user",
                "local_cols": ["user_id"],
                "remote_cols": ["id"],
            },
            {
                "new_constraint_name": "fk_api_token_client_id",
                "referred_table": "oauth_client",
                "local_cols": ["client_id"],
                "remote_cols": ["identifier"],
            },
        ],
    )

    _downgrade_recreate_foreign_keys(
        connection=connection,
        table_name="oauth_code",
        fk_definitions=[
            {
                "new_constraint_name": "fk_oauth_code_user_id",
                "referred_table": "user",
                "local_cols": ["user_id"],
                "remote_cols": ["id"],
            },
            {
                "new_constraint_name": "fk_oauth_code_client_id",
                "referred_table": "oauth_client",
                "local_cols": ["client_id"],
                "remote_cols": ["identifier"],
            },
        ],
    )

    op.drop_table("alembic_fk_metadata")

    if dialect == "sqlite":
        connection.execute(text("PRAGMA foreign_keys=ON;"))
