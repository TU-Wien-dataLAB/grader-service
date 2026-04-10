# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
import json
import secrets
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from grader_service import orm
from grader_service.api.models.assignment_settings import AssignmentSettings
from grader_service.file_services.git_files_service import construct_git_dir
from grader_service.handlers import GitRepoType
from grader_service.orm import Assignment, Lecture, Role, Submission, SubmissionLogs, User
from grader_service.orm.base import DeleteState
from grader_service.orm.submission import AutoStatus, FeedbackStatus, ManualStatus
from grader_service.orm.submission_properties import SubmissionProperties
from grader_service.orm.takepart import Scope
from grader_service.server import GraderServer


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
    a.properties = json.dumps({"notebooks": {}})
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


def insert_default_user(ex: Engine) -> None:
    session: Session = sessionmaker(ex)()
    session.add(User(name="ubuntu", display_name="ubuntu"))
    session.commit()


def create_user_submission_with_repo(
    engine: Engine, gitbase_dir: Path, student: User, assignment_id: int, lecture_code: str
) -> Submission:
    """Creates a submission for `student` and a user repo for storing it.

    Note: `gitbase_dir` should be based on the pytest `tmp_path` fixture, so that the test does not
    interfere with the file system.
    """
    # 1. Create and configure a student repo (a bare one, as a remote)
    submission_repo_path = construct_git_dir(
        gitbase_dir, GitRepoType.USER, lecture_code, assignment_id, username=student.name
    )
    submission_repo_path.mkdir(parents=True)
    subprocess.run(["git", "init", "--bare"], cwd=submission_repo_path, check=True)

    # 2. Create a "local" repo, create and commit a submission file, push to the remote
    tmp_repo_path = gitbase_dir / "tmp" / lecture_code / str(assignment_id) / "user" / student.name
    tmp_repo_path.mkdir(parents=True)
    subprocess.run(["git", "init"], cwd=tmp_repo_path, check=True)
    subprocess.run(
        ["git", "remote", "add", "origin", str(submission_repo_path)], cwd=tmp_repo_path, check=True
    )
    submission_file = tmp_repo_path / "submission.ipynb"
    submission_file.write_text("User submission content")
    subprocess.run(["git", "add", "--all"], cwd=tmp_repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Student submission"], cwd=tmp_repo_path, check=True)
    subprocess.run(["git", "push", "-u", "origin", "main"], cwd=tmp_repo_path, check=True)

    # 3. Create a submission object in the database
    commit_hash = (
        subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=tmp_repo_path, check=True, capture_output=True
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
    l_code: str,
    a_id: int,
    repo_type: GitRepoType,
    s_id: int | None = None,
    username: str | None = None,
    init_repo: bool = False,
):
    """Creates the directory where the repo of the given `repo_type` should be located.

    Note: this function does not actually init a Git repo unless `init_repo` is set to `True`.
    """
    git_dir = Path(app.grader_service_dir) / "git"
    git_dir.mkdir(exist_ok=True)
    repo_dir = construct_git_dir(
        git_dir, repo_type, l_code, a_id, submission_id=s_id, username=username
    )
    repo_dir.mkdir(parents=True, exist_ok=True)
    if init_repo:
        subprocess.run(["git", "init", "--bare"], cwd=repo_dir, check=True)
        tmp_base = Path(app.grader_service_dir) / "tmp"
        tmp_repo_dir = tmp_base / repo_type
        try:
            tmp_base.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "clone", repo_dir], cwd=tmp_base, check=True)
            submission_file = tmp_repo_dir / "submission.ipynb"
            submission_file.write_text(f"Test content for {repo_type} repo")
            subprocess.run(["git", "add", "-A"], cwd=tmp_repo_dir, check=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=tmp_repo_dir, check=True)
            subprocess.run(["git", "push", "origin", "main"], cwd=tmp_repo_dir, check=True)
        finally:
            shutil.rmtree(tmp_repo_dir)

    assert repo_dir.exists()


def create_all_git_repositories(app: GraderServer, user: User, l_code: str, a_id: int, s_id: int):
    """Creates all possible git repositories for a submission."""
    create_git_repository(
        app=app,
        l_code=l_code,
        a_id=a_id,
        repo_type=GitRepoType.SOURCE,
        s_id=s_id,
        username=user.name,
    )
    create_git_repository(
        app=app,
        l_code=l_code,
        a_id=a_id,
        repo_type=GitRepoType.RELEASE,
        s_id=s_id,
        username=user.name,
    )
    create_git_repository(
        app=app, l_code=l_code, a_id=a_id, repo_type=GitRepoType.USER, s_id=s_id, username=user.name
    )
    create_git_repository(
        app=app, l_code=l_code, a_id=a_id, repo_type=GitRepoType.EDIT, s_id=s_id, username=user.name
    )
    create_git_repository(
        app=app,
        l_code=l_code,
        a_id=a_id,
        repo_type=GitRepoType.AUTOGRADE,
        s_id=s_id,
        username=user.name,
    )
    create_git_repository(
        app=app,
        l_code=l_code,
        a_id=a_id,
        repo_type=GitRepoType.FEEDBACK,
        s_id=s_id,
        username=user.name,
    )

    check_git_repositories(app, user, l_code, a_id, s_id, True, True, True, True, True, True, True)


def check_git_repositories(
    app: GraderServer,
    user: User,
    l_code: str,
    a_id: int,
    s_id: int,
    exists_assignment: bool,
    exists_source: bool,
    exists_release: bool,
    exists_user: bool,
    exists_edit: bool,
    exists_feedback: bool,
    exists_autograde: bool,
):
    assignment_path = Path(app.grader_service_dir) / "git" / l_code / str(a_id)

    source_path = assignment_path / GitRepoType.SOURCE
    release_path = assignment_path / GitRepoType.RELEASE
    user_path = assignment_path / GitRepoType.USER / user.name
    edit_path = assignment_path / GitRepoType.EDIT / str(s_id)
    feedback_path = assignment_path / GitRepoType.FEEDBACK / "user" / user.name
    autograde_path = assignment_path / GitRepoType.AUTOGRADE / "user" / user.name

    assert assignment_path.exists() == exists_assignment
    assert source_path.exists() == exists_source
    assert release_path.exists() == exists_release
    assert user_path.exists() == exists_user
    assert edit_path.exists() == exists_edit
    assert feedback_path.exists() == exists_feedback
    assert autograde_path.exists() == exists_autograde
