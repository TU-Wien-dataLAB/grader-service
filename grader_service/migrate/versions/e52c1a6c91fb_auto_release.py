"""auto release

Revision ID: e52c1a6c91fb
Revises: a0718dae969d
Create Date: 2024-10-09 13:21:54.080731

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e52c1a6c91fb'
down_revision = 'a0718dae969d'
branch_labels = None
depends_on = None

new_enum = sa.Enum(
    'created', 'pushed', 'released', 'fetching', 'fetched', 'complete', 'release_scheduled',
    name='assignment_status'
)


def upgrade():
    # Sqlite doesn't support ALTER table, so make backup of status column, drop original status column and make a new one wit new enum values
    op.add_column('assignment', sa.Column('status_backup', sa.String(), nullable=True))
    op.execute("UPDATE assignment SET status_backup = status")
    op.drop_column('assignment', 'status')
    new_enum.create(op.get_bind(), checkfirst=True)
    op.add_column('assignment', sa.Column('status', new_enum, nullable=True))
    op.execute("UPDATE assignment SET status = status_backup")
    op.drop_column('assignment', 'status_backup')


def downgrade():
    # Remove 'release_scheduled' from assignment status options
    op.add_column('assignment', sa.Column('status_backup', sa.String(), nullable=True))

    op.execute(" UPDATE assignment SET status_backup = status")

    op.drop_column('assignment', 'status')
    old_enum = sa.Enum(
        'created', 'pushed', 'released', 'fetching', 'fetched', 'complete',
        name='assignment_status'
    )
    old_enum.create(op.get_bind(), checkfirst=True)
    op.add_column('assignment', sa.Column('status', old_enum, nullable=True))

    # If assignment status was 'release_scheduled' after downgrade it should be 'created' as the assignment is still not 'released'
    op.execute("""
            UPDATE assignment 
            SET status = CASE 
                WHEN status_backup = 'release_scheduled' THEN 'created'
                ELSE status_backup 
            END;
        """)

    op.drop_column('assignment', 'status_backup')
    new_enum.drop(op.get_bind(), checkfirst=True)
