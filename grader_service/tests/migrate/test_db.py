import pytest
from sqlalchemy.exc import IntegrityError

from grader_service.orm import Assignment as AssignmentORM
from grader_service.orm import Submission
from grader_service.tests.handlers.db_util import insert_submission


def test_foreign_key_constraints_in_sqlite(
    enable_foreign_keys_for_sqlite, sql_alchemy_engine, sql_alchemy_sessionmaker, default_user
):
    """Make sure the FK constraints are enabled in SQLite on engine connection."""

    # Note: in principle, tests use an sqlite db by default (see the `alembic_test.ini` file),
    # but some tests run with PostgreSQL.
    # We use the `enable_foreign_keys_for_sqlite` fixture to make sure the event listener
    # that enables FKs support for sqlite is disabled after this test.

    a_id = 1  # This assignment exists in the test database
    session = sql_alchemy_sessionmaker()
    engine = session.get_bind()
    sub = insert_submission(engine, a_id, "ubuntu", 1)

    with pytest.raises(IntegrityError, match="FOREIGN KEY constraint failed"):
        # Try to delete an existing assignment with a submission
        session.query(AssignmentORM).filter(AssignmentORM.id == a_id).delete()
        session.commit()

    assign = session.query(AssignmentORM).filter(AssignmentORM.id == a_id).one_or_none()
    sub_2 = session.query(Submission).filter(Submission.id == sub.id).one_or_none()
    assert assign is not None
    assert sub_2.id == assign.submissions[0].id
    session.close()
