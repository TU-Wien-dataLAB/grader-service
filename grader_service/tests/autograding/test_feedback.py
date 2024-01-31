# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import secrets
from grader_service.orm.assignment import Assignment
import pytest
from grader_service.server import GraderServer
import json
from grader_service.orm.submission import Submission
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from grader_service.autograding.local_feedback import GenerateFeedbackExecutor
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm.session import Session

# Imports are important otherwise they will not be found
from ..handlers.tornado_test_utils import *
from ..handlers.db_util import insert_submission
from sqlalchemy.orm import sessionmaker

from ...orm.submission_properties import SubmissionProperties


async def test_feedback(
        default_user,
        sql_alchemy_db,
        tmpdir
):
    default_user["groups"] = ["20wle2:instructor", "21wle1:instructor", "22wle1:instructor"]
    a_id = 1
    s_id = 1

    engine: Engine = sql_alchemy_db.engine
    insert_submission(engine, a_id, default_user["name"])

    session: Session = sessionmaker(bind=engine)()
    submission = session.query(Submission).get(s_id)
    submission_properties = session.query(SubmissionProperties).get(s_id)
    assert submission is not None
    assert submission_properties is not None
    gradebook_content = '{"notebooks":{}}'
    submission_properties.properties = gradebook_content  # we do not actually run convert so the gradebook can be empty
    session.commit()

    assert submission.score is None

    service_dir = str(tmpdir.mkdir("grader_service"))

    with patch.object(GenerateFeedbackExecutor, "_run_subprocess", return_value=None):
        executor = GenerateFeedbackExecutor(service_dir, submission)
        tmpdir.mkdir("grader_service/in")
        tmpdir.mkdir("grader_service/out")
        executor.relative_input_path = "in"
        executor.base_output_path = "out"

        await executor.start()

    submission = session.query(Submission).get(s_id)
    assert submission.feedback_available
