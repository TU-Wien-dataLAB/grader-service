# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from grader_service.api.models.assignment_settings import AssignmentSettings
from grader_service.orm import Assignment, Lecture, Role, Submission
from grader_service.orm.base import DeleteState
from grader_service.orm.submission import AutoStatus, FeedbackStatus, ManualStatus
from grader_service.orm.submission_properties import SubmissionProperties
from grader_service.orm.takepart import Scope


def add_role(engine: Engine, user_id: int, l_id: int, scope: Scope) -> Role:
    session: Session = sessionmaker(engine)()
    role = Role(user_id=user_id, lectid=l_id, role=scope)
    session.add(role)
    session.commit()
    session.flush()
    return role


def _get_lecture(id, name, code):
    lec = Lecture()
    lec.id = id
    lec.name = name
    lec.code = code
    lec.state = "active"
    lec.deleted = "active"
    return lec


def insert_lectures(session: Engine):
    session: Session = sessionmaker(session)()
    session.add(_get_lecture(1, "lecture1", "21wle1"))
    session.add(_get_lecture(2, "lecture2", "20wle2"))
    session.add(_get_lecture(3, "lecture2", "22wle1"))
    # session.add(_get_lecture("lecture3", "22sle3"))
    # session.add(_get_lecture("lecture4", "21sle4"))
    session.commit()
    session.flush()


def _get_assignment(name, lectid, points, status, settings):
    a = Assignment()
    a.name = name
    a.lectid = lectid
    a.points = points
    a.status = status
    a.settings = settings
    a.deleted = DeleteState.active
    a.properties = None
    return a


def insert_assignments(ex, lecture_id=1):
    session: Session = sessionmaker(ex)()
    session.add(
        _get_assignment(
            "assignment_1",
            lecture_id,
            20,
            "released",
            AssignmentSettings(deadline=datetime.now(tz=timezone.utc) + timedelta(weeks=2)),
        )
    )
    session.add(
        _get_assignment(
            "assignment_2",
            lecture_id,
            10,
            "created",
            AssignmentSettings(deadline=datetime.now(tz=timezone.utc) + timedelta(weeks=1)),
        )
    )
    session.commit()
    session.flush()
    num_inserts = 2
    return num_inserts


def _get_submission(
    assignment_id: int,
    username: str,
    user_id: int,
    feedback: FeedbackStatus = FeedbackStatus.NOT_GENERATED,
    score: Optional[float] = None,
):
    s = Submission()
    s.date = datetime.now(tz=timezone.utc)
    s.auto_status = AutoStatus.NOT_GRADED
    s.manual_status = ManualStatus.NOT_GRADED
    s.assignid = assignment_id
    s.user_id = user_id
    s.display_name = username
    s.score = score
    s.commit_hash = secrets.token_hex(20)
    s.feedback_status = feedback
    return s


def insert_submission(
    ex: Engine,
    assignment_id: int = 1,
    username: Optional[str] = "ubuntu",
    user_id: Optional[int] = 1,
    feedback: FeedbackStatus = FeedbackStatus.NOT_GENERATED,
    with_properties: bool = True,
    score: float = None,
):
    # TODO Allows only one submission with properties per user because we do not have
    #  the submission id
    session: Session = sessionmaker(ex)()
    session.add(_get_submission(assignment_id, username, user_id, feedback=feedback, score=score))
    session.commit()

    if with_properties:
        id = (
            session.query(Submission)
            .filter(Submission.assignid == assignment_id, Submission.user_id == user_id)
            .first()
            .id
        )
        session.add(SubmissionProperties(sub_id=id, properties=None))
        session.commit()
    session.flush()
