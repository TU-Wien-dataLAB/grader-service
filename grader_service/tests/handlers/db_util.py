# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
import os
import secrets
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from unittest.mock import Mock

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from grader_service import orm
from grader_service.api.models.assignment_settings import AssignmentSettings
from grader_service.handlers import GitRepoType
from grader_service.handlers.git.server import GitBaseHandler
from grader_service.orm import Assignment, Lecture, Role, Submission, SubmissionLogs, User
from grader_service.orm.base import DeleteState
from grader_service.orm.submission import AutoStatus, FeedbackStatus, ManualStatus
from grader_service.orm.submission_properties import SubmissionProperties
from grader_service.orm.takepart import Scope
from grader_service.server import GraderServer
from grader_service.tests.handlers.test_git import get_query_side_effect


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
    session.add(_get_lecture(3, "lecture3", "22wle1"))
    session.add(_get_lecture(4, "lecture4", "23wle1"))
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


def insert_assignment(ex, lecture_id=1):
    session: Session = sessionmaker(ex)()
    session.add(
        _get_assignment(
            "assignment_1",
            lecture_id,
            20,
            "created",
            AssignmentSettings(deadline=datetime.now(tz=timezone.utc) + timedelta(weeks=2)),
        )
    )
    session.commit()
    session.flush()
    num_inserts = 1
    return num_inserts


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
    commit_hash: Optional[str] = None,
):
    s = Submission()
    s.date = datetime.now(tz=timezone.utc)
    s.auto_status = AutoStatus.NOT_GRADED
    s.manual_status = ManualStatus.NOT_GRADED
    s.assignid = assignment_id
    s.user_id = user_id
    s.display_name = username
    s.score = score
    s.commit_hash = commit_hash or secrets.token_hex(20)
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
    commit_hash: Optional[str] = None,
    with_logs: bool = False,
) -> Submission:
    # TODO Allows only one submission with properties per user because we do not have
    #  the submission id
    session: Session = sessionmaker(ex)()
    submission = _get_submission(
        assignment_id, username, user_id, feedback=feedback, score=score, commit_hash=commit_hash
    )
    session.add(submission)
    session.commit()

    if with_properties:
        session.add(SubmissionProperties(sub_id=submission.id, properties=None))
        session.commit()

    if with_logs:
        session.add(SubmissionLogs(sub_id=submission.id, logs=None))
        session.commit()

    session.refresh(submission)
    session.flush()
    return submission


def insert_student(ex: Engine, username: str, lecture_id: int) -> User:
    """Creates a user with a student role in the specified lecture."""
    session: Session = sessionmaker(ex)(expire_on_commit=False)
    session.add(User(name=username, display_name=username))
    session.commit()
    user = session.query(User).filter(User.name == username).one()
    session.add(Role(user_id=user.id, lectid=lecture_id, role=Scope.student))
    session.commit()
    return user


def create_user_submission_with_repo(
    engine: Engine, gitbase_dir: Path, student: User, assignment_id: int, lecture_code: str
) -> Submission:
    """Creates a submission for `student` and a user repo for storing it.

    Note: `gitbase_dir` should be based on the pytest `tmp_path` fixture, so that the test does not
    interfere with the file system.
    """
    # 1. Create and configure a student repo (a bare one, as a remote)
    # TODO: This way of creating repo paths is brittle. We should have a function that does it.
    submission_repo_path = gitbase_dir / lecture_code / str(assignment_id) / "user" / student.name
    submission_repo_path.mkdir(parents=True)
    subprocess.run(
        ["git", "init", "--bare", "--initial-branch=main"], cwd=submission_repo_path, check=True
    )

    # 2. Create a "local" repo, create and commit a submission file, push to the remote
    tmp_repo_path = gitbase_dir / "tmp" / lecture_code / str(assignment_id) / "user" / student.name
    tmp_repo_path.mkdir(parents=True)
    subprocess.run(["git", "init", "--initial-branch=main"], cwd=tmp_repo_path, check=True)
    subprocess.run(
        ["git", "remote", "add", "origin", str(submission_repo_path)], cwd=tmp_repo_path, check=True
    )
    submission_file = tmp_repo_path / "submission.ipynb"
    submission_file.write_text("content")
    subprocess.run(["git", "add", "--all"], cwd=tmp_repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Student submission"], cwd=tmp_repo_path, check=True)
    subprocess.run(["git", "push", "-u", "origin", "main"], cwd=tmp_repo_path, check=True)

    # 3. Create a submission object in the database
    commit_hash = (
        subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=tmp_repo_path,
            check=True,
            capture_output=True,
        )
        .stdout.strip()
        .decode()
    )
    submission = insert_submission(
        engine, assignment_id, student.name, user_id=student.id, commit_hash=commit_hash
    )
    return submission


def check_assignment_and_status(
    engine: Engine, l_id: int, a_id: int, status: str, should_exist: bool = True
):
    session: Session = sessionmaker(engine)()
    assignment = (
        session.query(orm.Assignment)
        .filter(orm.Assignment.id == a_id, orm.Assignment.lectid == l_id)
        .first()
    )
    if should_exist:
        assert assignment is not None, "assignment is None"
        assert assignment.status == status, f"assert '{assignment.status}' == '{status}'"
    else:
        assert assignment is None, f"assignment exists (id={a_id}, lectid={l_id})"


def check_submission(engine: Engine, a_id: int, s_id: int, should_exist: bool = True):
    session: Session = sessionmaker(engine)()
    submission = (
        session.query(orm.Submission)
        .filter(orm.Submission.id == s_id, orm.Submission.assignid == a_id)
        .first()
    )
    if should_exist:
        assert submission is not None, "submission is None"
    else:
        assert submission is None, f"submission exists (id={s_id}, assignid={a_id})"


def create_git_repository(
    app: GraderServer,
    l_id: int,
    code: str,
    a_id: int,
    s_id: int,
    repo_type: GitRepoType,
    username: str,
):
    git_dir = Path(app.grader_service_dir) / "git"
    git_dir.mkdir(exist_ok=True)
    path = f"/git/{code}/{a_id}/{repo_type}/{s_id}"
    handler_mock = Mock()
    handler_mock.request.path = path
    handler_mock.gitbase = str(git_dir)
    handler_mock.user.name = username
    sf = get_query_side_effect(
        lid=l_id, code=code, scope=Scope.instructor, a_id=a_id, s_id=s_id, username=username
    )
    handler_mock.session.query = Mock(side_effect=sf)
    constructed_git_dir = GitBaseHandler.construct_git_dir(
        handler_mock,
        repo_type=repo_type,
        lecture=sf(orm.Lecture).filter().one(),
        assignment=sf(orm.Assignment).filter().one(),
        submission=sf(orm.Submission).filter().one(),
    )
    handler_mock.construct_git_dir = Mock(return_value=constructed_git_dir)
    lookup_dir = GitBaseHandler.gitlookup(handler_mock, "send-pack")
    assert os.path.exists(lookup_dir)


def create_all_git_repositories(
    app: GraderServer, user: User, l_id: int, l_code: str, a_id: int, s_id: int
):
    # create possible git repositories for submission
    create_git_repository(
        app=app,
        l_id=l_id,
        code=l_code,
        a_id=a_id,
        s_id=s_id,
        repo_type=GitRepoType.SOURCE,
        username=user.name,
    )
    create_git_repository(
        app=app,
        l_id=l_id,
        code=l_code,
        a_id=a_id,
        s_id=s_id,
        repo_type=GitRepoType.RELEASE,
        username=user.name,
    )
    create_git_repository(
        app=app,
        l_id=l_id,
        code=l_code,
        a_id=a_id,
        s_id=s_id,
        repo_type=GitRepoType.USER,
        username=user.name,
    )
    create_git_repository(
        app=app,
        l_id=l_id,
        code=l_code,
        a_id=a_id,
        s_id=s_id,
        repo_type=GitRepoType.EDIT,
        username=user.name,
    )
    create_git_repository(
        app=app,
        l_id=l_id,
        code=l_code,
        a_id=a_id,
        s_id=s_id,
        repo_type=GitRepoType.AUTOGRADE,
        username=user.name,
    )
    create_git_repository(
        app=app,
        l_id=l_id,
        code=l_code,
        a_id=a_id,
        s_id=s_id,
        repo_type=GitRepoType.FEEDBACK,
        username=user.name,
    )

    check_git_repositories(app, user, l_code, a_id, s_id, True, True, True, True, True, True, True)


def check_git_repositories(
    app: GraderServer,
    user: User,
    l_code: str,
    a_id: int,
    s_id: int,
    exits_assignment: bool,
    exits_source: bool,
    exits_release: bool,
    exits_user: bool,
    exits_edit: bool,
    exits_feedback: bool,
    exits_autograde: bool,
):
    assignment_path = Path(app.grader_service_dir) / "git" / l_code / str(a_id)

    source_path = assignment_path / GitRepoType.SOURCE
    release_path = assignment_path / GitRepoType.RELEASE
    user_path = assignment_path / GitRepoType.USER / user.name
    edit_path = assignment_path / GitRepoType.EDIT / str(s_id)
    feedback_path = assignment_path / GitRepoType.FEEDBACK / "user" / user.name
    autograde_path = assignment_path / GitRepoType.AUTOGRADE / "user" / user.name

    assert assignment_path.exists() if exits_assignment else not assignment_path.exists()
    assert source_path.exists() if exits_source else not source_path.exists()
    assert release_path.exists() if exits_release else not release_path.exists()
    assert user_path.exists() if exits_user else not user_path.exists()
    assert edit_path.exists() if exits_edit else not edit_path.exists()
    assert feedback_path.exists() if exits_feedback else not feedback_path.exists()
    assert autograde_path.exists() if exits_autograde else not autograde_path.exists()
