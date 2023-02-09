# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

from grader_service.orm.assignment import Assignment
import pytest
from grader_service.orm.submission import Submission
from unittest.mock import patch
from grader_service.autograding.local_grader import LocalAutogradeExecutor
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm.session import Session

# Imports are important otherwise they will not be found
from ..handlers.tornado_test_utils import default_user, sql_alchemy_db, db_test_config
from ..handlers.db_util import insert_submission, insert_assignments
from sqlalchemy.orm import sessionmaker


async def test_auto_grading(
        default_user,
        sql_alchemy_db,
        tmpdir
):
    l_id = 3  # default user is instructor
    a_id = 3
    s_id = 1

    engine: Engine = sql_alchemy_db.engine
    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user["name"])

    session: Session = sessionmaker(bind=engine)()
    submission = session.query(Submission).get(s_id)
    assert submission is not None
    assignment: Assignment = submission.assignment
    gradebook_content = '{"notebooks":{}}'
    assignment.properties = gradebook_content  # we do not actually run convert so the gradebook can be empty
    session.commit()

    assert submission.score is None

    service_dir = str(tmpdir.mkdir("grader_service"))

    with patch.object(LocalAutogradeExecutor, "_run_subprocess", return_value=None):
        executor = LocalAutogradeExecutor(service_dir, submission)
        tmpdir.mkdir("grader_service/in")
        tmpdir.mkdir("grader_service/out")
        executor.relative_input_path = "in"
        executor.relative_output_path = "out"

        await executor.start()

    submission = session.query(Submission).get(s_id)
    assert submission.properties.properties == gradebook_content  # because no actual autograding this is the same as assignment properties
    assert submission.auto_status == "automatically_graded"
    assert submission.score == 0  # we do not get any scores because of dummy gradebook, but it is set to 0

@pytest.mark.asyncio
async def test_auto_grading_pending(
        default_user,
        sql_alchemy_db,
        tmpdir
):
    l_id = 3  # default user is instructor
    a_id = 3
    s_id = 1

    engine: Engine = sql_alchemy_db.engine
    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user["name"])

    session: Session = sessionmaker(bind=engine)()
    submission = session.query(Submission).get(s_id)
    assert submission is not None
    assignment: Assignment = submission.assignment
    gradebook_content = '{"notebooks":{}}'
    assignment.properties = gradebook_content  # we do not actually run convert so the gradebook can be empty
    session.commit()

    service_dir = str(tmpdir.mkdir("grader_service"))

    with patch.object(LocalAutogradeExecutor, "_run_subprocess", return_value=None):
        executor = LocalAutogradeExecutor(service_dir, submission)
        tmpdir.mkdir("grader_service/in")
        tmpdir.mkdir("grader_service/out")
        executor.relative_input_path = "in"
        executor.relative_output_path = "out"

        await executor._pull_submission()

    submission = session.query(Submission).get(s_id)
    assert submission.auto_status == "pending"
