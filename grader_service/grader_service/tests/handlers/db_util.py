# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import secrets
from datetime import datetime

from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session

from grader_service.orm import Lecture, Assignment, Submission
from grader_service.orm.assignment import AutoGradingBehaviour
from grader_service.orm.base import DeleteState
from grader_service.orm.submission_properties import SubmissionProperties


def insert_users(session):
    session.execute('INSERT INTO "user" ("name") VALUES ("user1")')
    session.execute('INSERT INTO "user" ("name") VALUES ("user2")')
    session.execute('INSERT INTO "user" ("name") VALUES ("user3")')
    session.execute('INSERT INTO "user" ("name") VALUES ("user4")')


def _get_lecture(name, code):
    l = Lecture()
    l.name = name
    l.code = code
    l.state = "active"
    l.deleted = "active"
    return l


def insert_lectures(session: Engine):
    session: Session = sessionmaker(session)()
    session.add(_get_lecture("lecture1", "21wle1"))
    session.add(_get_lecture("lecture1", "21sle1"))
    session.add(_get_lecture("lecture2", "20wle2"))
    session.add(_get_lecture("lecture3", "22sle3"))
    session.add(_get_lecture("lecture4", "21sle4"))
    session.commit()
    session.flush()


def _get_assignment(name, lectid, due_date, points, status):
    a = Assignment()
    a.name = name
    a.lectid = lectid
    a.duedate = datetime.fromisoformat(due_date)
    a.points = points
    a.status = status
    a.allow_files = False
    a.automatic_grading = AutoGradingBehaviour.unassisted
    a.deleted = DeleteState.active
    a.max_submissions = None
    a.properties = None
    return a


def insert_assignments(ex, lecture_id=1):
    session: Session = sessionmaker(ex)()
    session.add(_get_assignment("assignment_1", lecture_id, "2055-06-06 23:59:00.000", 20, "released"))
    session.add(_get_assignment("assignment_2", lecture_id, "2055-07-07 23:59:00.000", 10, "created"))
    session.commit()
    session.flush()
    num_inserts = 2
    return num_inserts


def _get_submission(assignment_id, username, feedback=False, score=None):
    s = Submission()
    s.date = datetime.now()
    s.auto_status = "not_graded"
    s.manual_status = "not_graded"
    s.assignid = assignment_id
    s.username = username
    s.score = score
    s.commit_hash = secrets.token_hex(20)
    s.feedback_available = feedback
    return s


def _get_submission_properties(submission_id, properties=None):
    s = SubmissionProperties(sub_id=submission_id, properties=properties)
    return s


def insert_submission(ex, assignment_id=1, username="ubuntu", feedback=False, with_properties=True, score=None):
    # TODO Allows only one submission with properties per user because we do not have the submission id
    session: Session = sessionmaker(ex)()
    session.add(_get_submission(assignment_id, username, feedback=feedback, score=score))
    session.commit()
    if with_properties:
        id = session.query(Submission).filter(Submission.assignid==assignment_id,Submission.username==username).first().id
        session.add(_get_submission_properties(id))
        session.commit()
    session.flush()


def insert_take_part(ex, lecture_id, username="ubuntu", role="student"):
    ex.execute(f'INSERT INTO "takepart" ("username","lectid","role") VALUES ("{username}",{lecture_id},"{role}")')


def insert_grading(session):
    pass
