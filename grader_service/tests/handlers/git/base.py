from unittest.mock import Mock

import pytest
from tornado.web import HTTPError

from grader_service.handlers.git.base import RepoType, RPC, GitBaseHandler
from grader_service.orm import Role, User, Submission
from grader_service.orm.takepart import Scope

student_role = Role(role=Scope.student)
instructor_role = Role(role=Scope.instructor)

rpc = [RPC.UPLOAD_PACK, RPC.SEND_PACK, RPC.RECEIVE_PACK]

test_cases = [
    *[(instructor_role, RepoType.SOURCE, r, True) for r in rpc],
    *[(instructor_role, RepoType.USER_ASSIGNMENT, r, True) for r in rpc],
    *[(instructor_role, RepoType.GROUP_ASSIGNMENT, r, True) for r in rpc],
    *[(instructor_role, RepoType.EDIT, r, True) for r in rpc],
    *[(instructor_role, RepoType.RELEASE, r, True) for r in rpc],
    (instructor_role, RepoType.FEEDBACK, RPC.UPLOAD_PACK, True),
    (instructor_role, RepoType.AUTOGRADE, RPC.UPLOAD_PACK, True),
    # No auth for push
    *[(instructor_role, RepoType.FEEDBACK, r, False) for r in rpc[1:]],
    *[(instructor_role, RepoType.AUTOGRADE, r, False) for r in rpc[1:]],

    *[(student_role, RepoType.USER_ASSIGNMENT, r, True) for r in rpc],
    *[(student_role, RepoType.GROUP_ASSIGNMENT, r, True) for r in rpc],
    *[(student_role, RepoType.SOURCE, r, False) for r in rpc],
    *[(student_role, RepoType.AUTOGRADE, r, False) for r in rpc],
    *[(student_role, RepoType.EDIT, r, False) for r in rpc],
    # release gets pushed by grader service so students do not need pull
    *[(student_role, RepoType.RELEASE, r, False) for r in rpc],
    # feedback pull not allowed if submission is None
    (student_role, RepoType.FEEDBACK, RPC.UPLOAD_PACK, False),
    # No auth for push
    *[(student_role, RepoType.FEEDBACK, r, False) for r in rpc[1:]],
]


@pytest.mark.parametrize("role,repo_type,rpc,is_authorized", test_cases)
def test_auth(role, repo_type, rpc, is_authorized):
    handler_mock = Mock()
    handler_mock.role = role
    handler_mock.repo_type = repo_type
    handler_mock.rpc = rpc

    if is_authorized:
        GitBaseHandler.check_authorization(handler_mock)
    else:
        with pytest.raises(HTTPError):
            GitBaseHandler.check_authorization(handler_mock)


def test_student_feedback_auth():
    handler_mock = Mock()
    handler_mock.role = student_role
    handler_mock.repo_type = RepoType.FEEDBACK
    handler_mock.rpc = RPC.UPLOAD_PACK
    handler_mock.user = User(name="test")
    handler_mock.submission = Submission(username="test")

    GitBaseHandler.check_authorization(handler_mock)


def test_student_feedback_auth_username_error():
    handler_mock = Mock()
    handler_mock.role = student_role
    handler_mock.repo_type = RepoType.FEEDBACK
    handler_mock.rpc = RPC.UPLOAD_PACK
    handler_mock.user = User(name="test")
    handler_mock.submission = Submission(username="other")

    with pytest.raises(HTTPError):
        GitBaseHandler.check_authorization(handler_mock)
