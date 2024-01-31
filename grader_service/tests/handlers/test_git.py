# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
from http import HTTPStatus

from unittest import mock
from grader_service.orm.assignment import Assignment
from grader_service.orm.group import Group
from grader_service.orm.submission import Submission
from grader_service.orm.takepart import Role, Scope
import pytest
from unittest.mock import Mock
from grader_service.handlers.git.server import GitBaseHandler
from grader_service.orm.lecture import Lecture
from tornado.web import HTTPError
from .db_util import *
import os


def get_query_side_effect(lid=1, code="ivs21s", a_type="user", scope=Scope.student, group="test_group",
                          username="test_user", a_id=1):
    def query_side_effect(input):
        m = Mock()
        if input is Lecture:
            lecture = Lecture()
            lecture.id = lid
            lecture.code = code
            m.filter.return_value.one.return_value = lecture
        elif input is Assignment:
            assignment = Assignment()
            assignment.id = a_id
            assignment.type = a_type
            m.filter.return_value.one.return_value = assignment
        elif input is Role:
            role = Role()
            role.role = scope
            m.get.return_value = role
        elif input is Group:
            g = Group()
            g.name = group
            m.get.return_value = g
        elif input is Submission:
            sub = Submission()
            sub.username = username
            m.get.return_value = sub
        else:
            m.filter.return_value.one.return_value = None
        return m

    return query_side_effect


def test_git_lookup_instructor(tmpdir):
    path = "services/grader/git/iv21s/1/source"
    git_dir = str(tmpdir.mkdir("git"))

    handler_mock = Mock()
    handler_mock.request.path = path
    handler_mock.gitbase = git_dir
    handler_mock.user.name = "test_user"
    # handler_mock.session = session

    # orm mocks
    sf = get_query_side_effect(code="iv21s", a_type="group", scope=Scope.instructor)
    handler_mock.session.query = Mock(side_effect=sf)
    constructed_git_dir = GitBaseHandler.construct_git_dir(handler_mock, repo_type="source",
                                                           lecture=sf(Lecture).filter().one(),
                                                           assignment=sf(Assignment).filter().one())
    handler_mock.construct_git_dir = Mock(return_value=constructed_git_dir)

    lookup_dir = GitBaseHandler.gitlookup(handler_mock, "send-pack")

    assert os.path.exists(lookup_dir)
    assert os.path.exists(os.path.join(lookup_dir, "HEAD"))  # is git dir
    common_path = os.path.commonpath([git_dir, lookup_dir])
    created_paths = os.path.relpath(lookup_dir, common_path)
    assert created_paths == "iv21s/1/source"


def test_git_lookup_release_pull_instructor(tmpdir):
    path = "services/grader/git/iv21s/1/release"
    git_dir = str(tmpdir.mkdir("git"))

    handler_mock = Mock()
    handler_mock.request.path = path
    handler_mock.gitbase = git_dir
    handler_mock.user.name = "test_user"
    # handler_mock.session = session

    # orm mocks
    sf = get_query_side_effect(code="iv21s", a_type="user", scope=Scope.instructor)
    handler_mock.session.query = Mock(side_effect=sf)
    constructed_git_dir = GitBaseHandler.construct_git_dir(handler_mock, repo_type="release",
                                                           lecture=sf(Lecture).filter().one(),
                                                           assignment=sf(Assignment).filter().one())
    handler_mock.construct_git_dir = Mock(return_value=constructed_git_dir)

    lookup_dir = GitBaseHandler.gitlookup(handler_mock, "upload-pack")

    assert os.path.exists(lookup_dir)
    assert os.path.exists(os.path.join(lookup_dir, "HEAD"))  # is git dir
    common_path = os.path.commonpath([git_dir, lookup_dir])
    created_paths = os.path.relpath(lookup_dir, common_path)
    assert created_paths == "iv21s/1/release"


def test_git_lookup_release_push_student_error(tmpdir):
    path = "services/grader/git/iv21s/assign_1/release"
    pathlets = path.strip("/").split("/")[3:]
    git_dir = str(tmpdir.mkdir("git"))

    handler_mock = Mock()
    handler_mock.request.path = path
    handler_mock.gitbase = git_dir
    handler_mock.user.name = "test_user"
    # handler_mock.session = session

    # orm mocks
    sf = get_query_side_effect(code="iv21s", a_type="user", scope=Scope.student)
    handler_mock.session.query = Mock(side_effect=sf)
    role = sf(Role).get()

    with pytest.raises(HTTPError) as e, pytest.warns(DeprecationWarning):  # some deprecation warning in jupyter_server
        GitBaseHandler._check_git_repo_permissions(handler_mock, "send-pack", role, pathlets)
    assert e.value.status_code == 403


def test_git_lookup_source_push_student_error(tmpdir):
    path = "services/grader/git/iv21s/assign_1/source"
    pathlets = path.strip("/").split("/")[3:]
    git_dir = str(tmpdir.mkdir("git"))

    handler_mock = Mock()
    handler_mock.request.path = path
    handler_mock.gitbase = git_dir
    handler_mock.user.name = "test_user"
    # handler_mock.session = session

    # orm mocks
    sf = get_query_side_effect(code="iv21s", a_type="user", scope=Scope.student)
    handler_mock.session.query = Mock(side_effect=sf)
    role = sf(Role).get()

    with pytest.raises(HTTPError) as e, pytest.warns(DeprecationWarning):  # some deprecation warning in jupyter_server
        GitBaseHandler._check_git_repo_permissions(handler_mock, "send-pack", role, pathlets)
    assert e.value.status_code == 403


def test_git_lookup_source_push_student_error(tmpdir):
    path = "services/grader/git/iv21s/assign_1/source"
    pathlets = path.strip("/").split("/")[3:]
    git_dir = str(tmpdir.mkdir("git"))

    handler_mock = Mock()
    handler_mock.request.path = path
    handler_mock.gitbase = git_dir
    handler_mock.user.name = "test_user"
    # handler_mock.session = session

    # orm mocks
    sf = get_query_side_effect(code="iv21s", a_type="user", scope=Scope.student)
    handler_mock.session.query = Mock(side_effect=sf)
    role = sf(Role).get()

    with pytest.raises(HTTPError) as e, pytest.warns(DeprecationWarning):  # some deprecation warning in jupyter_server
        GitBaseHandler._check_git_repo_permissions(handler_mock, "send-pack", role, pathlets)
    assert e.value.status_code == 403

def mock_git_lookup(rpc: str):
    if rpc == "bad":
        return None
    else:
        return "/path/to"


def test_get_gitdir_not_found(tmpdir):
    handler_mock = Mock()
    handler_mock.request.path = "/abc"
    handler_mock.gitlookup = mock_git_lookup
    with pytest.raises(HTTPError) as e:
        GitBaseHandler.get_gitdir(handler_mock, "bad")
    assert e.value.status_code == HTTPStatus.NOT_FOUND


def test_get_gitdir(tmpdir):
    handler_mock = Mock()
    handler_mock.request.path = "/abc"
    handler_mock.gitlookup = mock_git_lookup
    path = GitBaseHandler.get_gitdir(handler_mock, "/abc")
    assert path == "/path/to"


def test_git_lookup_push_autograde_instructor_error():
    path = "services/grader/git/iv21s/assign_1/autograde"
    pathlets = path.strip("/").split("/")[3:]
    git_dir = "/tmp"

    handler_mock = Mock()
    handler_mock.request.path = path
    handler_mock.gitbase = git_dir
    handler_mock.user.name = "test_user"

    sf = get_query_side_effect(code="iv21s", scope=Scope.instructor)
    handler_mock.session.query = Mock(side_effect=sf)
    role = sf(Role).get()

    with pytest.raises(HTTPError) as e:
        GitBaseHandler._check_git_repo_permissions(handler_mock, "send-pack", role, pathlets)
    assert e.value.status_code == 403


def test_git_lookup_push_autograde_student_error():
    path = "services/grader/git/iv21s/assign_1/autograde"
    pathlets = path.strip("/").split("/")[3:]
    git_dir = "/tmp"

    handler_mock = Mock()
    handler_mock.request.path = path
    handler_mock.gitbase = git_dir
    handler_mock.user.name = "test_user"

    sf = get_query_side_effect(code="iv21s", scope=Scope.student)
    handler_mock.session.query = Mock(side_effect=sf)
    role = sf(Role).get()
    with pytest.raises(HTTPError) as e:
        GitBaseHandler._check_git_repo_permissions(handler_mock, "send-pack", role, pathlets)
    assert e.value.status_code == 403


def test_git_lookup_push_feedback_instructor_error():
    path = "services/grader/git/iv21s/assign_1/feedback"
    pathlets = path.strip("/").split("/")[3:]
    git_dir = "/tmp"

    handler_mock = Mock()
    handler_mock.request.path = path
    handler_mock.gitbase = git_dir
    handler_mock.user.name = "test_user"

    sf = get_query_side_effect(code="iv21s", scope=Scope.instructor)
    handler_mock.session.query = Mock(side_effect=sf)
    role = sf(Role).get()
    with pytest.raises(HTTPError) as e:
        GitBaseHandler._check_git_repo_permissions(handler_mock, "send-pack", role, pathlets)
    assert e.value.status_code == 403


def test_git_lookup_push_feedback_student_error():
    path = "services/grader/git/iv21s/assign_1/feedback"
    pathlets = path.strip("/").split("/")[3:]
    git_dir = "/tmp"

    handler_mock = Mock()
    handler_mock.request.path = path
    handler_mock.gitbase = git_dir
    handler_mock.user.name = "test_user"

    sf = get_query_side_effect(code="iv21s", scope=Scope.student)
    handler_mock.session.query = Mock(side_effect=sf)
    role = sf(Role).get()
    with pytest.raises(HTTPError) as e:
        GitBaseHandler._check_git_repo_permissions(handler_mock, "send-pack", role, pathlets)
    assert e.value.status_code == 403


def test_git_lookup_pull_autograde_instructor(tmpdir):
    path = "services/grader/git/iv21s/1/autograde/1"
    git_dir = str(tmpdir.mkdir("git"))

    handler_mock = Mock()
    handler_mock.request.path = path
    handler_mock.gitbase = git_dir
    handler_mock.user.name = "test_user"

    # orm mocks
    sf = get_query_side_effect(code="iv21s", a_type="user", scope=Scope.instructor)
    handler_mock.session.query = Mock(side_effect=sf)
    role_mock = Mock()
    role_mock.role = Scope.instructor
    handler_mock.get_role = Mock(return_value=role_mock)
    constructed_git_dir = GitBaseHandler.construct_git_dir(handler_mock, repo_type="autograde",
                                                           lecture=sf(Lecture).filter().one(),
                                                           assignment=sf(Assignment).filter().one(),
                                                           submission=sf(Submission).get())
    handler_mock.construct_git_dir = Mock(return_value=constructed_git_dir)

    lookup_dir = GitBaseHandler.gitlookup(handler_mock, "upload-pack")

    assert os.path.exists(lookup_dir)
    assert os.path.exists(os.path.join(lookup_dir, "HEAD"))  # is git dir
    common_path = os.path.commonpath([git_dir, lookup_dir])
    created_paths = os.path.relpath(lookup_dir, common_path)
    assert created_paths == "iv21s/1/autograde/user/test_user"


def test_git_lookup_pull_autograde_student_error():
    path = "services/grader/git/iv21s/assign_1/autograde"
    pathlets = path.strip("/").split("/")[3:]
    git_dir = "/tmp"

    handler_mock = Mock()
    handler_mock.request.path = path
    handler_mock.gitbase = git_dir
    handler_mock.user.name = "test_user"

    sf = get_query_side_effect(code="iv21s", scope=Scope.student)
    handler_mock.session.query = Mock(side_effect=sf)
    role = sf(Role).get()

    with pytest.raises(HTTPError) as e:
        GitBaseHandler._check_git_repo_permissions(handler_mock, "upload-pack", role, pathlets)
    assert e.value.status_code == 403


def test_git_lookup_pull_feedback_instructor(tmpdir):
    path = "services/grader/git/iv21s/1/feedback/1"
    git_dir = str(tmpdir.mkdir("git"))

    handler_mock = Mock()
    handler_mock.request.path = path
    handler_mock.gitbase = git_dir
    handler_mock.user.name = "test_user"

    # orm mocks
    sf = get_query_side_effect(code="iv21s", a_type="user", scope=Scope.instructor)
    handler_mock.session.query = Mock(side_effect=sf)
    constructed_git_dir = GitBaseHandler.construct_git_dir(handler_mock, repo_type="feedback",
                                                           lecture=sf(Lecture).filter().one(),
                                                           assignment=sf(Assignment).filter().one())
    handler_mock.construct_git_dir = Mock(return_value=constructed_git_dir)

    lookup_dir = GitBaseHandler.gitlookup(handler_mock, "upload-pack")

    assert os.path.exists(lookup_dir)
    assert os.path.exists(os.path.join(lookup_dir, "HEAD"))  # is git dir
    common_path = os.path.commonpath([git_dir, lookup_dir])
    created_paths = os.path.relpath(lookup_dir, common_path)
    assert created_paths == "iv21s/1/feedback/user/test_user"


def test_git_lookup_pull_feedback_student_with_valid_id(tmpdir):
    path = "services/grader/git/iv21s/1/feedback/1"
    git_dir = str(tmpdir.mkdir("git"))

    handler_mock = Mock()
    handler_mock.request.path = path
    handler_mock.gitbase = git_dir
    handler_mock.user.name = "test_user"

    # orm mocks
    sf = get_query_side_effect(code="iv21s", a_type="user", scope=Scope.student, username="test_user")
    handler_mock.session.query = Mock(side_effect=sf)
    constructed_git_dir = GitBaseHandler.construct_git_dir(handler_mock, repo_type="feedback",
                                                           lecture=sf(Lecture).filter().one(),
                                                           assignment=sf(Assignment).filter().one())
    handler_mock.construct_git_dir = Mock(return_value=constructed_git_dir)

    lookup_dir = GitBaseHandler.gitlookup(handler_mock, "upload-pack")

    assert os.path.exists(lookup_dir)
    assert os.path.exists(os.path.join(lookup_dir, "HEAD"))  # is git dir
    common_path = os.path.commonpath([git_dir, lookup_dir])
    created_paths = os.path.relpath(lookup_dir, common_path)
    assert created_paths == "iv21s/1/feedback/user/test_user"


def test_git_lookup_pull_feedback_student_with_valid_id_extra(tmpdir):
    path = "services/grader/git/iv21s/1/feedback/1/info/refs&service=git-upload-pack"
    git_dir = str(tmpdir.mkdir("git"))

    handler_mock = Mock()
    handler_mock.request.path = path
    handler_mock.gitbase = git_dir
    handler_mock.user.name = "test_user"

    # orm mocks
    sf = get_query_side_effect(code="iv21s", a_type="user", scope=Scope.student, username="test_user")
    handler_mock.session.query = Mock(side_effect=sf)
    constructed_git_dir = GitBaseHandler.construct_git_dir(handler_mock, repo_type="feedback",
                                                           lecture=sf(Lecture).filter().one(),
                                                           assignment=sf(Assignment).filter().one())
    handler_mock.construct_git_dir = Mock(return_value=constructed_git_dir)

    lookup_dir = GitBaseHandler.gitlookup(handler_mock, "upload-pack")

    assert os.path.exists(lookup_dir)
    assert os.path.exists(os.path.join(lookup_dir, "HEAD"))  # is git dir
    common_path = os.path.commonpath([git_dir, lookup_dir])
    created_paths = os.path.relpath(lookup_dir, common_path)
    assert created_paths == "iv21s/1/feedback/user/test_user"


def test_git_lookup_pull_feedback_student_with_invalid_id_error():
    path = "services/grader/git/iv21s/assign_1/feedback/1"
    pathlets = path.strip("/").split("/")[3:]
    git_dir = "/tmp"

    handler_mock = Mock()
    handler_mock.request.path = path
    handler_mock.gitbase = git_dir
    handler_mock.user.name = "test_user"

    # test that submission with id 1 comes from "other_user"
    sf = get_query_side_effect(code="iv21s", a_type="user", scope=Scope.student, username="other_user")
    handler_mock.session.query = Mock(side_effect=sf)
    role = sf(Role).get()

    with pytest.raises(HTTPError) as e:
        GitBaseHandler._check_git_repo_permissions(handler_mock, "upload-pack", role, pathlets)
    assert e.value.status_code == 403


# /services/grader/git/20wle2/Assignment%201/feedback/2/info/refs&service=git-upload-pack
def test_git_lookup_pull_feedback_student_no_id_error():
    path = "services/grader/git/iv21s/assign_1/feedback"
    pathlets = path.strip("/").split("/")[3:]
    git_dir = "/tmp"

    handler_mock = Mock()
    handler_mock.request.path = path
    handler_mock.gitbase = git_dir
    handler_mock.user.name = "test_user"

    sf = get_query_side_effect(code="iv21s", scope=Scope.student)
    handler_mock.session.query = Mock(side_effect=sf)
    role = sf(Role).get()

    with pytest.raises(HTTPError) as e:
        GitBaseHandler._check_git_repo_permissions(handler_mock, "upload-pack", role, pathlets)
    assert e.value.status_code == 403


def test_git_lookup_pull_feedback_student_no_id_error_extra():
    path = "/services/grader/git/20wle2/Assignment%201/feedback/info/refs&service=git-upload-pack"
    pathlets = path.strip("/").split("/")[3:]
    git_dir = "/tmp"

    handler_mock = Mock()
    handler_mock.request.path = path
    handler_mock.gitbase = git_dir
    handler_mock.user.name = "test_user"

    sf = get_query_side_effect(code="iv21s", scope=Scope.student)
    handler_mock.session.query = Mock(side_effect=sf)
    role = sf(Role).get()

    with pytest.raises(HTTPError) as e:
        GitBaseHandler._check_git_repo_permissions(handler_mock, "upload-pack", role, pathlets)
    assert e.value.status_code == 403


def test_git_lookup_pull_feedback_student_bad_id_error():
    path = "services/grader/git/iv21s/assign_1/feedback/abc/"
    pathlets = path.strip("/").split("/")[3:]
    git_dir = "/tmp"

    handler_mock = Mock()
    handler_mock.request.path = path
    handler_mock.gitbase = git_dir
    handler_mock.user.name = "test_user"

    sf = get_query_side_effect(code="iv21s", scope=Scope.student)
    handler_mock.session.query = Mock(side_effect=sf)
    role = sf(Role).get()

    with pytest.raises(HTTPError) as e:
        GitBaseHandler._check_git_repo_permissions(handler_mock, "upload-pack", role, pathlets)
    assert e.value.status_code == 403
