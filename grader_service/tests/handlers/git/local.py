import os
import shlex
import subprocess
from pathlib import Path
from unittest.mock import Mock

import pytest

from grader_service.handlers.git.base import RepoType
from grader_service.handlers.git.local import GitLocalServer
from grader_service.orm import User, Lecture, Submission

repo_types = [RepoType.USER_ASSIGNMENT, RepoType.GROUP_ASSIGNMENT, RepoType.RELEASE, RepoType.SOURCE, RepoType.EDIT,
              RepoType.FEEDBACK, RepoType.AUTOGRADE]


@pytest.fixture()
def git_local_server(tmpdir):
    return GitLocalServer.instance(grader_service_dir=str(tmpdir))


# since assignment repos duplicate the release repo on creation they are tested there
@pytest.mark.parametrize("repo_type", repo_types[2:])
def test_create_repo(git_local_server, repo_type):
    user = User(name="test")
    assignment = Mock()
    assignment.id = 1
    assignment.lecture = Lecture(code="lect")
    assignment.type = "user"
    submission = Submission(id=10, username=user.name)

    git_local_server.create_repo(repo_type, user, assignment, submission)
    git_dir = git_local_server.git_location(repo_type, user, assignment, submission)
    assert os.path.isdir(git_dir)
    assert git_local_server.is_base_git_dir(git_dir)


def test_duplicate_release(git_local_server, tmpdir):
    user = User(name="test_user")
    assignment = Mock()
    assignment.id = 1
    assignment.lecture = Lecture(code="lect")
    assignment.type = "user"

    git_local_server.create_repo(RepoType.RELEASE, user, assignment)
    release_path = Path(git_local_server.git_location(RepoType.RELEASE, user, assignment))
    assert release_path.exists()

    release_push_dir = Path(str(tmpdir)) / "release"
    release_push_dir.mkdir()
    subprocess.run(shlex.split('git init'), cwd=release_push_dir)
    (release_push_dir / "test.py").touch()
    subprocess.run(shlex.split('git add -A'), cwd=release_push_dir)
    subprocess.run(shlex.split('git commit -m "test"'), cwd=release_push_dir)
    subprocess.run(shlex.split(f'git push --set-upstream {release_path} main'), cwd=release_push_dir)

    git_local_server.create_repo(RepoType.USER_ASSIGNMENT, user, assignment)
    user_path = Path(git_local_server.git_location(RepoType.USER_ASSIGNMENT, user, assignment))

    git_local_server.duplicate_release_repo(user, assignment)

    user_clone_dir = Path(str(tmpdir)) / "user"
    user_clone_dir.mkdir()
    subprocess.run(shlex.split(f'git clone {user_path} -b main'), cwd=user_clone_dir)
    assert (user_clone_dir / user.name / "test.py").exists()
