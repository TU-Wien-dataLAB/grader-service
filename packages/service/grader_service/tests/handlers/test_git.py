# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
import os
from http import HTTPStatus
from pathlib import Path
from unittest.mock import Mock

import pytest
from tornado.web import HTTPError

from grader_service.file_services import SubmissionGitFileService
from grader_service.handlers.git.server import GitBaseHandler
from grader_service.handlers.handler_utils import GitRepoType
from grader_service.orm import User
from grader_service.orm.assignment import Assignment
from grader_service.orm.lecture import Lecture
from grader_service.orm.submission import Submission
from grader_service.orm.takepart import Role, Scope

_REQUEST_PATH_TEMPLATE = "/git/iv21s/1/{repo_type}/{tail}"


def _create_lecture(l_id: int = 1, code: str = "iv21s") -> Lecture:
    lecture = Lecture()
    lecture.id = l_id
    lecture.code = code
    return lecture


def _create_assignment(a_id: int = 1, l_id: int = 1) -> Assignment:
    assignment = Assignment()
    assignment.id = a_id
    assignment.lectid = l_id
    return assignment


def _create_role(l_id: int = 1, user_id: int = 137, scope: Scope = Scope.student) -> Role:
    role = Role()
    role.role = scope
    role.lectid = l_id
    role.user_id = user_id
    return role


def _create_submission(s_id: int, user_id: int, username: str) -> Submission:
    sub = Submission()
    sub.id = s_id
    sub.user_id = user_id
    sub.user = User(id=user_id, name=username)
    sub.assignment = _create_assignment(a_id=1)
    sub.assignid = 1
    return sub


def get_query_side_effect(
    l_id=1,
    code="iv21s",
    scope: Scope = Scope.student,
    username="test_user",
    user_id=137,
    a_id=1,
    s_id=1,
    s_username=None,
    s_user_id=None,
):
    if s_username is None:
        s_username = username
    if s_user_id is None:
        s_user_id = user_id

    def query_side_effect(input):
        query = Mock()
        if input is Lecture:
            lecture = _create_lecture(l_id, code)
            query.filter.return_value.one.return_value = lecture
        elif input is Assignment:
            assignment = _create_assignment(a_id, l_id)
            query.filter.return_value.one.return_value = assignment
        elif input is Role:
            role = _create_role(l_id, user_id, scope)
            query.filter.return_value.one.return_value = role
        elif input is Submission:
            sub = _create_submission(s_id, s_user_id, s_username)
            query.get.return_value = sub
            query.filter.return_value.one.return_value = sub
        else:
            query.filter.return_value.one.return_value = None
        return query

    return query_side_effect


def get_get_side_effect(
    l_id=1,
    code="iv21s",
    scope: Scope = Scope.student,
    username="test_user",
    user_id=137,
    a_id=1,
    s_id=1,
    s_username="test_user",
    s_user_id=137,
):
    def get_side_effect(input, *args, **kwargs):
        if input is Lecture:
            return _create_lecture(l_id, code)
        elif input is Assignment:
            return _create_assignment(a_id, l_id)
        elif input is Role:
            return _create_role(l_id, user_id, scope)
        elif input is Submission:
            return _create_submission(s_id, s_user_id, s_username)
        return None

    return get_side_effect


@pytest.fixture
def git_handler_factory(app, default_user, default_user_login, sql_alchemy_engine, tmp_path):
    def _create_handler(
        req_path: str | None = None,
        repo_type: GitRepoType | None = GitRepoType.SOURCE,
        user: User | None = default_user,
        query_kw: dict | None = None,
    ) -> GitBaseHandler:
        if req_path is None:
            req_path = _REQUEST_PATH_TEMPLATE.format(repo_type=repo_type, tail="")
        if query_kw is None:
            query_kw = {}
        request = Mock(path=req_path)
        handler = GitBaseHandler(app, request)
        handler.application.grader_server_dir = tmp_path
        handler.request = request
        handler._grader_user = user
        handler.user.is_admin = False
        handler.session = Mock()
        handler.session.get = get_get_side_effect(**query_kw)
        handler.session.query.side_effect = get_query_side_effect(**query_kw)
        handler.file_service = Mock(spec=SubmissionGitFileService)

        return handler

    return _create_handler


def _create_release_dir(handler: GitBaseHandler):
    # For user repo_type, the release repo has to exist first
    lec = _create_lecture()
    a = _create_assignment()
    repo_path_release = GitBaseHandler.construct_git_dir(handler, GitRepoType.RELEASE, lec, a)
    os.makedirs(repo_path_release, exist_ok=True)


def mock_git_lookup(rpc: str):
    if rpc == "bad":
        return None
    else:
        return "/path/to"


def test_get_gitdir_not_found():
    handler_mock = Mock()
    handler_mock.gitlookup = mock_git_lookup
    with pytest.raises(HTTPError) as e:
        GitBaseHandler.get_gitdir(handler_mock, "bad")
    assert e.value.status_code == HTTPStatus.NOT_FOUND


def test_get_gitdir():
    handler_mock = Mock()
    handler_mock.gitlookup = mock_git_lookup
    path = GitBaseHandler.get_gitdir(handler_mock, "/abc")
    assert path == "/path/to"


# ===============  Allowed actions tests  ===============


@pytest.mark.parametrize("repo_type", [GitRepoType.SOURCE, GitRepoType.RELEASE])
def test_git_lookup_pull_instructor(git_handler_factory, repo_type):
    git_handler = git_handler_factory(repo_type=repo_type, query_kw={"scope": Scope.instructor})
    lookup_dir = GitBaseHandler.gitlookup(git_handler, "upload-pack")
    lookup_path = Path(lookup_dir)

    assert lookup_path.exists()
    assert (lookup_path / "HEAD").exists()  # is git dir
    assert lookup_path.is_relative_to(git_handler.gitbase)
    created_paths = lookup_path.relative_to(git_handler.gitbase)
    expected_path = f"iv21s/1/{repo_type}"
    assert created_paths == Path(expected_path)


@pytest.mark.parametrize(
    "repo_type, req_path_tail",
    [
        (GitRepoType.USER, "student-name"),  # should it be available??
        (GitRepoType.EDIT, 1),
        (GitRepoType.AUTOGRADE, 1),
        (GitRepoType.FEEDBACK, 1),
    ],
)
def test_git_lookup_pull_with_submission_instructor(git_handler_factory, repo_type, req_path_tail):
    req_path = _REQUEST_PATH_TEMPLATE.format(repo_type=repo_type, tail=req_path_tail)
    sub_id = 1
    student_name = "student-name"
    git_handler = git_handler_factory(
        req_path=req_path,
        query_kw={
            "scope": Scope.instructor,
            "s_id": sub_id,
            "s_username": student_name,
            "s_user_id": 2137,
        },
    )
    if repo_type == GitRepoType.USER:
        _create_release_dir(git_handler)

    lookup_dir = GitBaseHandler.gitlookup(git_handler, "upload-pack")
    lookup_path = Path(lookup_dir)

    assert lookup_path.exists()
    assert (lookup_path / "HEAD").exists()  # is git dir
    assert lookup_path.is_relative_to(git_handler.gitbase)
    created_paths = lookup_path.relative_to(git_handler.gitbase)

    # Note: the submission user is not the current user
    if repo_type == GitRepoType.USER:
        expected_path = f"iv21s/1/{repo_type}/{student_name}"
    elif repo_type == GitRepoType.EDIT:
        expected_path = f"iv21s/1/{repo_type}/{sub_id}"
    elif repo_type == GitRepoType.AUTOGRADE:
        expected_path = f"iv21s/1/{repo_type}/user/{student_name}"
    else:  # repo_type == GitRepoType.FEEDBACK
        expected_path = f"iv21s/1/{repo_type}/user/{git_handler.user.name}"
    assert created_paths == Path(expected_path)


@pytest.mark.parametrize("rpc_cmd", ["upload-pack", "receive-pack", "send-pack"])
def test_git_lookup_pull_user_student(git_handler_factory, rpc_cmd):
    repo_type = GitRepoType.USER
    git_handler = git_handler_factory(repo_type=repo_type)
    _create_release_dir(git_handler)

    lookup_dir = GitBaseHandler.gitlookup(git_handler, rpc_cmd)
    lookup_path = Path(lookup_dir)

    assert lookup_path.exists()
    assert (lookup_path / "HEAD").exists()  # is git dir
    assert lookup_path.is_relative_to(git_handler.gitbase)
    created_paths = lookup_path.relative_to(git_handler.gitbase)
    assert created_paths == Path(f"iv21s/1/{repo_type}/{git_handler.user.name}")


@pytest.mark.parametrize("req_path_tail", ["1", "1/info/refs&service=git-upload-pack"])
def test_git_lookup_pull_feedback_student_with_valid_id(git_handler_factory, req_path_tail):
    repo_type = GitRepoType.FEEDBACK
    req_path = _REQUEST_PATH_TEMPLATE.format(repo_type=repo_type, tail=req_path_tail)
    git_handler = git_handler_factory(req_path=req_path)

    lookup_dir = GitBaseHandler.gitlookup(git_handler, "upload-pack")
    lookup_path = Path(lookup_dir)

    assert lookup_path.exists()
    assert (lookup_path / "HEAD").exists()  # is git dir
    assert lookup_path.is_relative_to(git_handler.gitbase)
    created_paths = lookup_path.relative_to(git_handler.gitbase)
    assert created_paths == Path(f"iv21s/1/{repo_type}/user/{git_handler.user.name}")


# ===============  Forbidden actions tests  ===============


@pytest.mark.parametrize("repo_type", [GitRepoType.SOURCE, GitRepoType.RELEASE, GitRepoType.EDIT])
def test_git_lookup_push_student_error(git_handler_factory, repo_type):
    git_handler = git_handler_factory(repo_type=repo_type)

    with pytest.raises(HTTPError) as e:
        GitBaseHandler.gitlookup(git_handler, "send-pack")
    assert e.value.status_code == HTTPStatus.FORBIDDEN
    assert e.value.log_message == "forbidden action"


def test_git_lookup_pull_autograde_student_error(git_handler_factory):
    repo_type = GitRepoType.AUTOGRADE
    git_handler = git_handler_factory(repo_type=repo_type)

    with pytest.raises(HTTPError) as e:
        GitBaseHandler.gitlookup(git_handler, "upload-pack")
    assert e.value.status_code == HTTPStatus.FORBIDDEN
    assert e.value.log_message == "forbidden action"


@pytest.mark.parametrize("scope", [Scope.instructor, Scope.student])
@pytest.mark.parametrize("rpc_cmd", ["send-pack", "receive-pack"])
@pytest.mark.parametrize("repo_type", [GitRepoType.AUTOGRADE, GitRepoType.FEEDBACK])
def test_git_lookup_forbidden_actions_for_repo_types(
    git_handler_factory, repo_type, rpc_cmd, scope
):
    req_path = _REQUEST_PATH_TEMPLATE.format(repo_type=repo_type, tail="1")
    git_handler = git_handler_factory(req_path=req_path, query_kw={"scope": scope})

    with pytest.raises(HTTPError) as e:
        GitBaseHandler.gitlookup(git_handler, rpc_cmd)
    assert e.value.status_code == HTTPStatus.FORBIDDEN
    assert e.value.log_message == "forbidden action for the repo type"


def test_git_lookup_pull_feedback_student_with_invalid_id_error(git_handler_factory, tmp_path):
    l_code = "iv21s"
    repo_type = GitRepoType.FEEDBACK
    sub_id = 1
    path = f"/git/{l_code}/1/{repo_type}/{sub_id}"

    # test that submission with id 1 comes from "other_user"
    sf = get_query_side_effect(code=l_code, scope=Scope.student, username="other_user", user_id=999)
    role = sf(Role).get()
    git_handler = git_handler_factory(path, user=User(name="other_user", id=999))
    with pytest.raises(HTTPError) as e:
        GitBaseHandler._check_git_repo_permissions(
            git_handler, "upload-pack", role, repo_type, sub_id
        )
    assert e.value.status_code == 404
    assert e.value.log_message == "Submission not found"


def test_git_lookup_pull_feedback_student_no_id_error(git_handler_factory, tmp_path):
    repo_type = GitRepoType.FEEDBACK

    with pytest.raises(HTTPError) as e:
        GitBaseHandler.gitlookup(git_handler_factory(repo_type=repo_type), "upload-pack")
    assert e.value.status_code == 400
    assert e.value.log_message == "Invalid or missing submission id"


def test_git_lookup_pull_feedback_student_no_id_error_extra(git_handler_factory, tmp_path):
    # l_code = "20wle2"
    repo_type = GitRepoType.FEEDBACK
    path = _REQUEST_PATH_TEMPLATE.format(
        repo_type=repo_type, tail="info/refs&service=git-upload-pack"
    )

    with pytest.raises(HTTPError) as e:
        GitBaseHandler.gitlookup(git_handler_factory(path), "upload-pack")
    assert e.value.status_code == 400
    assert e.value.log_message == "Invalid or missing submission id"


def test_git_lookup_pull_feedback_student_bad_id_error(git_handler_factory, tmp_path):
    repo_type = GitRepoType.FEEDBACK
    sub_id = "abc"
    path = _REQUEST_PATH_TEMPLATE.format(repo_type=repo_type, tail=f"{sub_id}")

    with pytest.raises(HTTPError) as e:
        GitBaseHandler.gitlookup(git_handler_factory(path), "upload-pack")
    assert e.value.status_code == 400
    assert e.value.log_message == "Invalid or missing submission id"
