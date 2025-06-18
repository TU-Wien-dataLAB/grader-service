"""Added oauth provider functionality

Revision ID: ba71c755c153
Revises: 9cfeb0faa0c0
Create Date: 2023-08-18 10:30:24.465356

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKeyConstraint,
    Integer,
    PrimaryKeyConstraint,
    Text,
    Unicode,
)

from grader_service.utils import new_token

# revision identifiers, used by Alembic.
revision = "ba71c755c153"
down_revision = "9cfeb0faa0c0"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "api_token",
        Column("username", Unicode(255)),
        Column("id", Integer, nullable=True),
        Column("hashed", Unicode(255)),
        Column("prefix", Unicode(16)),
        Column("client_id", Unicode(255)),
        Column("session_id", Unicode(255)),
        Column("created", DateTime),
        Column("expires_at", DateTime),
        Column("last_activity", DateTime),
        Column("note", Unicode(1023)),
        Column("scopes", Text),
        PrimaryKeyConstraint("id"),
        ForeignKeyConstraint(["username"], ["user.name"]),
    )

    op.create_table(
        "oauth_client",
        Column("id", Integer, nullable=True),
        Column("identifier", Unicode(255), unique=True),
        Column("description", Unicode(1023)),
        Column("secret", Unicode(255)),
        Column("redirect_uri", Unicode(1023)),
        Column("allowed_scopes", Text),
        PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "oauth_code",
        Column("id", Integer, nullable=True),
        Column("client_id", Unicode(255)),
        Column("code", Unicode(36)),
        Column("expires_at", Integer),
        Column("redirect_uri", Unicode(1023)),
        Column("session_id", Unicode(255)),
        Column("username", Unicode(255)),
        Column("scopes", Text),
        PrimaryKeyConstraint("id"),
        ForeignKeyConstraint(["client_id"], ["oauth_client.identifier"]),
        ForeignKeyConstraint(["username"], ["user.name"]),
    )

    op.add_column("user", sa.Column("encrypted_auth_state", sa.types.LargeBinary, nullable=True))
    op.add_column("user", sa.Column("cookie_id", Unicode(255), nullable=True))

    connection = op.get_bind()
    result = connection.execute(sa.text('select * from "user"'))
    for row in result:
        connection.execute(
            sa.text('UPDATE "user" SET cookie_id = :uuid WHERE name = :name'),
            uuid=new_token(),
            name=row["name"],
        )

    if connection.dialect.name != "sqlite":
        op.alter_column("user", "cookie_id", nullable=False)
        op.create_unique_constraint("uq_user_cookie", "user", ["cookie_id"])
    else:
        with op.batch_alter_table("user") as batch_op:
            batch_op.alter_column("cookie_id", nullable=False)
            batch_op.create_unique_constraint("uq_user_cookie", ["cookie_id"])


def downgrade():
    connection = op.get_bind()
    op.drop_table("api_token")
    op.drop_table("oauth_code")
    op.drop_table("oauth_client")
    op.drop_column("user", "encrypted_auth_state")
    if connection.dialect.name != "sqlite":
        op.drop_constraint("uq_user_cookie", "user")
    else:
        with op.batch_alter_table("user") as batch_op:
            batch_op.drop_constraint("uq_user_cookie")

    op.drop_column("user", "cookie_id")
