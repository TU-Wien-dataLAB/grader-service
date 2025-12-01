# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
import csv
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from unittest.mock import MagicMock, patch

import isodate
import pytest
from sqlalchemy.orm import sessionmaker, Session
from tornado.httpclient import HTTPClientError

from grader_service.api.models import AssignmentSettings, Submission
from grader_service.handlers.submissions import (
    INSTRUCTOR_SUBMISSION_COMMIT_CASH,
    SubmissionEditHandler,
    SubmissionHandler,
)
from grader_service.orm import Assignment as AssignmentORM
from grader_service.orm import Role
from grader_service.orm.base import DeleteState
from grader_service.orm.submission import AutoStatus, FeedbackStatus, ManualStatus
from grader_service.orm.submission import Submission as SubmissionORM
from grader_service.orm.takepart import Scope
from grader_service.server import GraderServer
from .db_util import (
    create_user_submission_with_repo,
    insert_assignments,
    insert_student,
    insert_submission, check_submission, create_all_git_repositories, check_git_repositories,
)
from ... import orm


async def submission_test_setup(engine, default_user, a_id: int):
    insert_submission(engine, a_id, default_user.name, default_user.id)
    insert_submission(engine, a_id, default_user.name, default_user.id, with_properties=False)
    # should make no difference
    insert_submission(engine, a_id, "debian", 2)
    insert_submission(engine, a_id, "debian", 2, with_properties=False)


async def test_get_submissions_lecture_unauthorized(
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 1  # user is student
    a_id = 1
    s_id = 1
    insert_submission(sql_alchemy_engine, a_id, default_user.name, default_user.id)

    check_submission(sql_alchemy_engine, a_id, s_id)

    url = service_base_url + f"lectures/{l_id}/submissions/"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.FORBIDDEN


@pytest.mark.parametrize(
    "period,expected", [("P0D", 1.0), ("P1D", 0.5), ("P2D", 0.2), ("P3D", 0.1)]
)
def test_calculate_late_submission_scaling(period, expected):
    a = AssignmentORM()
    role = Role()
    role.role = Scope.student
    now = datetime.now(timezone.utc)

    settings = {
        "deadline": now,
        "late_submission": [
            {"period": "P1D", "scaling": 0.5},
            {"period": "P2D", "scaling": 0.2},
            {"period": "P3D", "scaling": 0.1},
        ],
    }
    a.settings = settings

    submission_ts = now - isodate.parse_duration("PT1S") + isodate.parse_duration(period)
    assert SubmissionHandler.calculate_late_submission_scaling(a, submission_ts, role) == expected


def test_calculate_late_submission_scaling_error():
    a = AssignmentORM()
    role = Role()
    role.role = Scope.student
    now = datetime.now(timezone.utc)

    settings = {"deadline": now, "late_submission": [{"period": "P1D", "scaling": 0.5}]}
    a.settings = settings

    submission_ts = now + isodate.parse_duration("P1M")
    from tornado.web import HTTPError

    with pytest.raises(HTTPError):
        SubmissionHandler.calculate_late_submission_scaling(a, submission_ts, role)


async def test_get_submissions(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
    default_user,
):
    a_id = 1
    url = service_base_url + f"lectures/1/assignments/{a_id}/submissions/"
    await submission_test_setup(sql_alchemy_engine, default_user, a_id)
    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK
    submissions = json.loads(response.body.decode())
    assert isinstance(submissions, list)
    assert len(submissions) == 2
    assert submissions[0]["user_id"] == default_user.id
    assert submissions[1]["user_id"] == default_user.id
    Submission.from_dict(submissions[0])


async def test_get_submissions_format_csv(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    a_id = 1
    url = service_base_url + f"lectures/1/assignments/{a_id}/submissions/?format=csv"
    await submission_test_setup(sql_alchemy_engine, default_user, a_id)

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK
    decoded_content = response.body.decode("utf-8")

    body_csv = csv.reader(decoded_content.splitlines(), delimiter=",")
    submissions = list(body_csv)
    # Delete column description
    submissions.pop(0)

    assert len(submissions) == 2
    assert submissions[0][4] == str(default_user.id)
    assert submissions[1][4] == str(default_user.id)
    assert submissions[0][5] == default_user.name
    assert submissions[1][5] == default_user.name


async def test_get_submissions_format_wrong(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 1  # default user is student
    a_id = 1

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/?format=abc"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.BAD_REQUEST


async def test_get_submissions_filter_wrong(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 1  # default user is student
    a_id = 1

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/?filter=abc"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.BAD_REQUEST


async def test_get_submissions_instructor_version(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 3
    a_id = 4
    engine = sql_alchemy_engine
    insert_assignments(engine, l_id)
    other_user = insert_student(engine, "student1", l_id)

    url = (
            service_base_url
            + f"lectures/{l_id}/assignments/{a_id}/submissions/?instructor-version=true"
    )

    insert_submission(engine, a_id, default_user.name, user_id=default_user.id)
    insert_submission(
        engine, a_id, default_user.name, user_id=default_user.id, with_properties=False
    )
    insert_submission(engine, a_id, other_user.name, user_id=other_user.id)
    insert_submission(engine, a_id, other_user.name, user_id=other_user.id, with_properties=False)

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK
    submissions = json.loads(response.body.decode())
    assert isinstance(submissions, list)
    assert len(submissions) == 4
    user_submission = submissions[0:2]

    possible_users = {default_user.id, other_user.id}
    user_id = submissions[0]["user_id"]
    assert user_id in possible_users
    possible_users.remove(user_id)

    assert isinstance(user_submission, list)
    assert len(user_submission) == 2
    assert all([isinstance(s, dict) for s in user_submission])
    [Submission.from_dict(s) for s in user_submission]

    user_submission = submissions[2:4]

    user_id = user_submission[0]["user_id"]
    assert user_id in possible_users
    possible_users.remove(user_id)
    assert len(possible_users) == 0

    assert isinstance(user_submission, list)
    assert len(user_submission) == 2
    assert all([isinstance(s, dict) for s in user_submission])
    [Submission.from_dict(s) for s in user_submission]


async def test_get_submissions_instructor_version_unauthorized(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 1  # default user is student
    a_id = 1
    engine = sql_alchemy_engine

    url = (
            service_base_url
            + f"lectures/{l_id}/assignments/{a_id}/submissions/?instructor-version=true"
    )

    insert_submission(engine, a_id, username=default_user.name, user_id=default_user.id)
    insert_submission(
        engine, a_id, username=default_user.name, user_id=default_user.id, with_properties=False
    )

    check_submission(sql_alchemy_engine, a_id, 1)
    check_submission(sql_alchemy_engine, a_id, 2)

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.FORBIDDEN


async def test_get_submissions_latest_instructor_version(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 3
    a_id = 4
    engine = sql_alchemy_engine
    insert_assignments(engine, l_id)
    other_user = insert_student(engine, "student1", l_id)

    url = (
            service_base_url
            + f"lectures/{l_id}/assignments/{a_id}/submissions/?instructor-version=true&filter=latest"
    )

    insert_submission(engine, a_id, default_user.name, user_id=default_user.id)
    insert_submission(
        engine, a_id, default_user.name, user_id=default_user.id, with_properties=False
    )
    insert_submission(engine, a_id, other_user.name, user_id=other_user.id)
    insert_submission(engine, a_id, other_user.name, user_id=other_user.id, with_properties=False)

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK
    submissions = json.loads(response.body.decode())
    assert isinstance(submissions, list)
    assert len(submissions) == 2
    # Submissions of first user
    user_submission = submissions[0:1]

    possible_users = {default_user.id, other_user.id}
    user_id = user_submission[0]["user_id"]
    assert user_id in possible_users
    possible_users.remove(user_id)

    assert isinstance(user_submission, list)
    assert len(user_submission) == 1
    assert all([isinstance(s, dict) for s in user_submission])
    [Submission.from_dict(s) for s in user_submission]

    user_submission = submissions[1:2]

    user_id = user_submission[0]["user_id"]
    assert user_id in possible_users
    possible_users.remove(user_id)
    assert len(possible_users) == 0

    assert isinstance(user_submission, list)
    assert len(user_submission) == 1
    assert all([isinstance(s, dict) for s in user_submission])
    [Submission.from_dict(s) for s in user_submission]


async def test_get_submissions_best_instructor_version(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 3
    a_id = 4
    engine = sql_alchemy_engine
    insert_assignments(engine, l_id)
    other_user = insert_student(engine, "student1", l_id)

    url = (
            service_base_url
            + f"lectures/{l_id}/assignments/{a_id}/submissions/?instructor-version=true&filter=best"
    )

    insert_submission(
        engine,
        a_id,
        default_user.name,
        user_id=default_user.id,
        feedback=FeedbackStatus.GENERATED,
        score=3,
    )
    insert_submission(
        engine,
        a_id,
        default_user.name,
        user_id=default_user.id,
        feedback=FeedbackStatus.NOT_GENERATED,
        with_properties=False,
    )
    insert_submission(engine, a_id, "user1", user_id=other_user.id, score=3)
    insert_submission(engine, a_id, "user1", user_id=other_user.id, with_properties=False)

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK
    submissions = json.loads(response.body.decode())
    assert isinstance(submissions, list)
    assert len(submissions) == 2
    # Submissions of first user
    user_submission = submissions[0:1]

    possible_users = {default_user.id, other_user.id}
    user_id = user_submission[0]["user_id"]
    assert user_id in possible_users
    possible_users.remove(user_id)

    assert isinstance(user_submission, list)
    assert len(user_submission) == 1
    assert all([isinstance(s, dict) for s in user_submission])
    [Submission.from_dict(s) for s in user_submission]


async def test_get_submissions_lecture_assignment_missmatch(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 3
    a_id = 1
    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND


async def test_get_submissions_wrong_assignment_id(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 1
    a_id = 99
    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND


async def test_get_submissions_deleted(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
    default_user,
):
    l_id = 1
    a_id = 1
    await submission_test_setup(sql_alchemy_engine, default_user, a_id)

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/1"
    response = await http_server_client.fetch(
        url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions"
    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK

    submissions = json.loads(response.body.decode())
    assert isinstance(submissions, list)
    assert len(submissions) == 1
    assert submissions[0]["user_id"] == default_user.id
    Submission.from_dict(submissions[0])


async def test_get_submissions_admin_deleted(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_admin_login,
    default_user,
    default_admin,
):
    l_id = 1
    a_id = 1
    await submission_test_setup(sql_alchemy_engine, default_user, a_id)

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/1"
    response = await http_server_client.fetch(
        url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions"
    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK

    submissions = json.loads(response.body.decode())
    assert isinstance(submissions, list)
    assert len(submissions) == 2
    assert submissions[0]["user_id"] == default_admin.id
    assert submissions[1]["user_id"] == default_admin.id
    Submission.from_dict(submissions[0])
    Submission.from_dict(submissions[1])


async def test_get_submissions_admin_deleted_instructor_version(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_admin_login,
    default_user,
    default_admin,
):
    l_id = 1
    a_id = 1
    await submission_test_setup(sql_alchemy_engine, default_user, a_id)

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/1"
    response = await http_server_client.fetch(
        url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions?instructor-version=true"
    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK

    submissions = json.loads(response.body.decode())
    assert isinstance(submissions, list)
    assert len(submissions) == 4
    assert submissions[0]["user_id"] == default_user.id
    assert submissions[1]["user_id"] == default_user.id
    assert submissions[2]["user_id"] == default_admin.id
    assert submissions[3]["user_id"] == default_admin.id
    Submission.from_dict(submissions[0])
    Submission.from_dict(submissions[1])
    Submission.from_dict(submissions[2])
    Submission.from_dict(submissions[3])


async def test_get_submission(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
    default_user,
):
    l_id = 3  # user has to be instructor
    a_id = 4
    engine = sql_alchemy_engine
    insert_assignments(engine, l_id)

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/1/"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND

    insert_submission(engine, a_id, default_user.name, default_user.id)

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK
    submission_dict = json.loads(response.body.decode())
    Submission.from_dict(submission_dict)


async def test_get_submission_assignment_lecture_missmatch(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 3  # user has to be instructor
    engine = sql_alchemy_engine
    insert_assignments(engine, l_id)

    a_id = 1  # assignment with a_id 1 is in l_id 1
    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/1/"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND


async def test_get_submission_assignment_submission_missmatch(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 3  # user has to be instructor
    a_id = 4
    engine = sql_alchemy_engine
    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user.name, default_user.id)

    check_submission(engine, a_id, 1)

    a_id = 1  # this assignment has no submissions
    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/1/"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND


async def test_get_submission_wrong_submission(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 3  # user has to be instructor
    a_id = 3
    engine = sql_alchemy_engine
    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user.name, default_user.id)

    check_submission(engine, a_id, 1)

    a_id = 1  # this assignment has no submissions
    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/99/"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND


async def test_get_submission_student_from_another_student(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
    default_admin,
):
    l_id = 1  # user has to be student
    a_id = 1
    s_id = 1
    engine = sql_alchemy_engine
    insert_submission(engine, a_id, default_admin.name, default_admin.id)

    check_submission(engine, a_id, s_id)

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/{s_id}/"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND


async def test_get_submission_admin_from_another_student(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_admin_login,
    default_admin,
):
    l_id = 1  # admon has no role
    a_id = 1
    s_id = 1
    engine = sql_alchemy_engine
    insert_submission(engine, a_id, default_user.name, default_user.id)

    check_submission(engine, a_id, s_id)

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/{s_id}/"

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK
    submission_dict = json.loads(response.body.decode())
    Submission.from_dict(submission_dict)


async def test_put_submission(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 3  # user has to be instructor
    a_id = 4
    s_id = 1

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/{s_id}/"

    engine = sql_alchemy_engine
    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user.name, default_user.id)

    pre_submission = Submission(
        id=-1,
        user_id=default_user.id,
        submitted_at=None,
        commit_hash=secrets.token_hex(20),
        auto_status=AutoStatus.AUTOMATICALLY_GRADED,
        manual_status=ManualStatus.MANUALLY_GRADED,
        feedback_status=FeedbackStatus.NOT_GENERATED,
    )
    response = await http_server_client.fetch(
        url,
        method="PUT",
        headers={"Authorization": f"Token {default_token}"},
        body=json.dumps(pre_submission.to_dict()),
    )
    assert response.code == HTTPStatus.OK
    submission_dict = json.loads(response.body.decode())
    submission = Submission.from_dict(submission_dict)
    assert submission.id == s_id
    assert submission.auto_status == pre_submission.auto_status
    assert submission.manual_status == pre_submission.manual_status
    assert submission.commit_hash != pre_submission.commit_hash  # commit hash cannot be changed
    assert submission.feedback_status == FeedbackStatus.NOT_GENERATED
    # assert submission.submitted_at.strftime("%Y-%m-%dT%H:%M:%S.%f")[0:-3]  == pre_submission.submitted_at
    assert submission.score is None


async def test_put_submission_lecture_assignment_missmatch(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 3
    a_id = 1
    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/1"

    engine = sql_alchemy_engine
    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user.name, default_user.id)

    now = datetime.now(timezone.utc).isoformat("T", "milliseconds")
    pre_submission = Submission(
        id=-1,
        user_id=default_user.id,
        submitted_at=now,
        commit_hash=secrets.token_hex(20),
        auto_status=AutoStatus.AUTOMATICALLY_GRADED,
        manual_status=ManualStatus.MANUALLY_GRADED,
        feedback_status=FeedbackStatus.NOT_GENERATED,
    )
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="PUT",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(pre_submission.to_dict()),
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND


async def test_put_submission_assignment_submission_missmatch(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 3  # user has to be instructor
    a_id = 3
    engine = sql_alchemy_engine
    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user.name, default_user.id)

    a_id = 1  # this assignment has no submissions
    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/1/"

    now = datetime.now(timezone.utc).isoformat("T", "milliseconds")
    pre_submission = Submission(
        id=-1,
        user_id=default_user.id,
        submitted_at=now,
        commit_hash=secrets.token_hex(20),
        auto_status=AutoStatus.AUTOMATICALLY_GRADED,
        manual_status=ManualStatus.MANUALLY_GRADED,
        feedback_status=FeedbackStatus.NOT_GENERATED,
    )
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="PUT",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(pre_submission.to_dict()),
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND


async def test_put_submission_wrong_submission(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 3  # user has to be instructor
    a_id = 3
    engine = sql_alchemy_engine
    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user.name, default_user.id)

    a_id = 1  # this assignment has no submissions
    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/99/"

    now = datetime.now(timezone.utc).isoformat("T", "milliseconds")
    pre_submission = Submission(
        id=-1,
        user_id=default_user.id,
        submitted_at=now,
        commit_hash=secrets.token_hex(20),
        auto_status=AutoStatus.AUTOMATICALLY_GRADED,
        manual_status=ManualStatus.MANUALLY_GRADED,
        feedback_status=FeedbackStatus.NOT_GENERATED,
    )
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="PUT",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(pre_submission.to_dict()),
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND


async def test_delete_own_submission_by_student(
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 1  # default user is student
    a_id = 1
    insert_submission(sql_alchemy_engine, a_id, default_user.name)

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/1/"
    response = await http_server_client.fetch(
        url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND

    session = sessionmaker(sql_alchemy_engine)()
    submission = session.query(SubmissionORM).get(1)
    assert submission.deleted == DeleteState.deleted


async def test_delete_submission(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
    sql_alchemy_engine,
    default_user,
):
    l_id = 1  # default user is student
    a_id = 1
    s_id = 1

    insert_submission(sql_alchemy_engine, a_id, default_user.name, default_user.id)

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/{s_id}"

    response = await http_server_client.fetch(
        url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK

    check_submission(sql_alchemy_engine, a_id, s_id)

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND


async def test_delete_submission_deleted_submission(
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 1  # default user is student
    a_id = 1
    s_id = 1

    insert_submission(sql_alchemy_engine, a_id, default_user.name, default_user.id)

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/{s_id}"

    response = await http_server_client.fetch(
        url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK

    check_submission(sql_alchemy_engine, a_id, s_id)

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND


async def test_delete_submission_not_found(
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 1  # default user is student
    a_id = 1
    s_id = 999

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/{s_id}"

    check_submission(sql_alchemy_engine, a_id, s_id, should_exist=False)

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND


async def test_delete_submission_student_from_another_student(
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 1  # default user is student
    a_id = 1
    s_id = 1

    # The submission does NOT belong to the default user:
    insert_submission(sql_alchemy_engine, a_id, "debian", 2)
    check_submission(sql_alchemy_engine, a_id, s_id)

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/{s_id}"
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND


async def test_delete_submission_admin_from_another_student(
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_admin_login,
):
    l_id = 1  # admin has no role
    a_id = 1
    s_id = 1

    # The submission does NOT belong to the admin:
    insert_submission(sql_alchemy_engine, a_id, default_user.name, default_user.id)

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/{s_id}"
    response = await http_server_client.fetch(
        url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK
    submission_dict = json.loads(response.body.decode())
    Submission.from_dict(submission_dict)

    session: Session = sessionmaker(sql_alchemy_engine)()
    submission = session.query(orm.Submission).filter(orm.Submission.id == s_id).first()
    assert submission.deleted == DeleteState.deleted


async def test_delete_submission_with_feedback(
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 1  # default user is student
    a_id = 1
    s_id = 1

    insert_submission(sql_alchemy_engine, a_id, default_user.name, feedback=FeedbackStatus.GENERATED)
    check_submission(sql_alchemy_engine, a_id, s_id)

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/{s_id}"
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.FORBIDDEN
    assert e.message == "Only submissions without feedback can be deleted."


async def test_delete_submission_after_deadline(
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 1  # default user is student
    a_id = 1
    s_id = 1

    session = sessionmaker(sql_alchemy_engine)()
    assign = session.query(AssignmentORM).get(1)
    assign.settings = {"deadline": datetime(1999, 6, 6, tzinfo=timezone.utc)}
    session.commit()
    session.flush()

    insert_submission(sql_alchemy_engine, a_id, default_user.name)

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/{s_id}"
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.FORBIDDEN
    assert e.message == "Submission can't be deleted, due date of assigment has passed."


async def test_delete_submission_hard(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_admin_login,
    sql_alchemy_engine,
    default_user,
):
    l_id = 1  # admin has no role
    a_id = 1
    s_id = 1

    insert_submission(sql_alchemy_engine, a_id, default_user.name, default_user.id, with_properties=True,
                      with_logs=True)

    session: Session = sessionmaker(sql_alchemy_engine)()
    submissions = session.query(orm.Submission).filter(orm.Submission.id == s_id).all()
    assert len(submissions) == 1
    submission_properties = session.query(orm.SubmissionProperties).filter(
        orm.SubmissionProperties.sub_id == s_id).all()
    assert len(submission_properties) == 1
    submission_logs = session.query(orm.SubmissionLogs).filter(orm.SubmissionLogs.sub_id == s_id).all()
    assert len(submission_logs) == 1

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/{s_id}"

    response = await http_server_client.fetch(
        url + "?hard_delete=true", method="DELETE", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK

    check_submission(sql_alchemy_engine, a_id, s_id, should_exist=False)

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND

    submissions = session.query(orm.Submission).filter(orm.Submission.id == s_id).all()
    assert len(submissions) == 0
    submission_properties = session.query(orm.SubmissionProperties).filter(
        orm.SubmissionProperties.sub_id == s_id).all()
    assert len(submission_properties) == 0
    submission_logs = session.query(orm.SubmissionLogs).filter(orm.SubmissionLogs.sub_id == s_id).all()
    assert len(submission_logs) == 0


async def test_delete_submission_hard_unauthorized(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
    sql_alchemy_engine,
    default_user,
):
    l_id = 1  # default user is student
    a_id = 1
    s_id = 1

    insert_submission(sql_alchemy_engine, a_id, default_user.name, default_user.id, with_properties=True,
                      with_logs=True)

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/{s_id}"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url + "?hard_delete=true", method="DELETE", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.FORBIDDEN


async def test_delete_submission_hard_with_files(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_admin_login,
    sql_alchemy_engine,
    default_user,
):
    l_id = 1  # admin has no role
    l_code = "21wle1"
    a_id = 1
    s_id = 1

    insert_submission(sql_alchemy_engine, a_id, default_user.name, default_user.id)
    create_all_git_repositories(app, default_user, l_id, l_code, a_id, s_id)

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/{s_id}"

    response = await http_server_client.fetch(
        url + "?hard_delete=true", method="DELETE", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK

    check_submission(sql_alchemy_engine, a_id, s_id, should_exist=False)

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND

    check_git_repositories(app, default_user, l_code, a_id, s_id,
                           True, True, True, False, False, False, False)


async def test_post_submission_by_student(
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 1  # default user is student
    a_id = 1

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/"

    with (
        patch("os.path.exists"),
        patch("subprocess.run"),
        patch("grader_service.autograding.celery.tasks.CeleryApp", autospec=True),
        patch("grader_service.handlers.submissions.chain", autospec=True) as mock_chain,
    ):
        resp = await http_server_client.fetch(
            url,
            method="POST",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps({"commit_hash": secrets.token_hex(20)}),
        )

    assert resp.code == HTTPStatus.ACCEPTED
    mock_chain.assert_called_once()


async def test_post_submission_by_instructor(
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_engine,
    tmp_path,
    default_roles,
    default_user_login,
):
    l_id = 3  # default user is instructor
    a_id = 3
    engine = sql_alchemy_engine
    insert_assignments(engine, l_id)
    student_username = "e.noether"
    insert_student(engine, student_username, l_id)

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/"

    with (
        patch("subprocess.run"),
        patch.object(SubmissionHandler, "construct_git_dir", str(tmp_path)),
        patch("grader_service.handlers.submissions.chain", autospec=True) as mock_chain,
    ):
        response = await http_server_client.fetch(
            url,
            method="POST",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(
                {"commit_hash": INSTRUCTOR_SUBMISSION_COMMIT_CASH, "username": student_username}
            ),
        )

    assert response.code == HTTPStatus.CREATED
    # When an instructor creates a submission, it should not be automatically graded
    mock_chain.assert_not_called()

    s_url = url + "1"
    s_resp = await http_server_client.fetch(
        s_url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert s_resp.code == HTTPStatus.OK
    submission_dict = json.loads(s_resp.body.decode())
    submission = Submission.from_dict(submission_dict)

    assert submission.user_display_name == student_username
    assert submission.auto_status == AutoStatus.NOT_GRADED


async def test_post_submission_git_repo_not_found(
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 1  # default user is student
    a_id = 1

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="POST",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps({"commit_hash": secrets.token_hex(20)}),
        )
    e = exc_info.value
    assert e.code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert e.message == "User git repository not found"


async def test_post_submission_commit_hash_not_found(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 3  # default user is instructor
    a_id = 3
    engine = sql_alchemy_engine
    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user.name, default_user.id)

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/"

    pre_submission = {"value": "10"}
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="POST",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(pre_submission),
        )
    e = exc_info.value
    assert e.code == HTTPStatus.BAD_REQUEST
    assert e.message == "Commit hash not found in body"


async def test_post_submission_max_submissions_assignment(
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_sessionmaker,
    default_roles,
    default_user_login,
):
    l_id = 1  # default user is student
    a_id = 3
    session = sql_alchemy_sessionmaker()

    # Set-up: Create an assignment with max_submissions = 1
    assignment_orm = AssignmentORM(
        name="pytest", lectid=l_id, points=20, status="released", deleted=DeleteState.active
    )
    assignment_orm.settings = AssignmentSettings(
        deadline=datetime.now(tz=timezone.utc) + timedelta(weeks=2),
        max_submissions=1,
        autograde_type="unassisted",
    )
    session.add(assignment_orm)
    session.commit()
    assert assignment_orm.id == 3

    # Post one submission to exhaust the submissions limit
    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/"
    post_body = {"commit_hash": secrets.token_hex(20)}

    with patch("subprocess.run"), patch("os.path.exists"):
        response = await http_server_client.fetch(
            url,
            method="POST",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(post_body),
        )
    assert response.code == HTTPStatus.CREATED

    # Posting another submission should fail
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="POST",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(post_body),
        )

    e = exc_info.value
    assert e.code == HTTPStatus.CONFLICT


async def test_submission_properties(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 3  # default user is instructor
    a_id = 4

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/1/properties"

    engine = sql_alchemy_engine
    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user.name, default_user.id)

    prop = {"notebooks": {}}
    put_response = await http_server_client.fetch(
        url,
        method="PUT",
        headers={"Authorization": f"Token {default_token}"},
        body=json.dumps(prop),
    )
    assert put_response.code == HTTPStatus.OK
    get_response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert get_response.code == HTTPStatus.OK
    assignment_props = json.loads(get_response.body.decode())
    assert assignment_props == prop


async def test_submission_properties_not_correct(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 3  # default user is instructor
    a_id = 4

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/1/properties"

    engine = sql_alchemy_engine
    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user.name, default_user.id)

    prop = "{}"
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="PUT",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(prop),
        )
    e = exc_info.value
    assert e.code == HTTPStatus.BAD_REQUEST
    assert e.message == "Cannot parse properties file!"


async def test_submission_properties_lecture_assignment_missmatch(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 3
    a_id = 1
    engine = sql_alchemy_engine
    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user.name, default_user.id)

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/1/properties"

    prop = {"test": "property", "value": 2, "bool": True, "null": None}

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="PUT",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(prop),
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND


async def test_submission_properties_assignment_submission_missmatch(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 3  # user has to be instructor
    a_id = 3
    engine = sql_alchemy_engine
    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user.name, default_user.id)

    a_id = 1  # this assignment has no submissions
    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/1/properties"

    prop = {"test": "property", "value": 2, "bool": True, "null": None}

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="PUT",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(prop),
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND


async def test_submission_properties_wrong_submission(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 3  # user has to be instructor
    a_id = 3
    engine = sql_alchemy_engine
    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user.name, default_user.id)

    a_id = 1  # this assignment has no submissions
    sub_id = 1  # this submission belongs to another assignment
    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/{sub_id}/properties"

    prop = {"test": "property", "value": 2, "bool": True, "null": None}

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="PUT",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(prop),
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND
    assert e.message == f"Submission with id {sub_id} was not found"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND
    assert e.message == "Properties of submission were not found"


async def test_submission_properties_not_found(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 3  # user has to be instructor
    a_id = 3
    engine = sql_alchemy_engine
    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user.name, default_user.id, with_properties=False)

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/1/properties"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND
    assert e.message == "Properties of submission were not found"


async def test_submission_create_edit_repo(
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
    tmp_path,
):
    """Create or reset an edit repository (there is no difference) - SubmissionEditHandler.put()"""
    l_id = 3  # default user has to be instructor
    l_code = "22wle1"  # the code of the lecture with id=3
    a_id = 3

    gitbase_dir = tmp_path / "git"

    engine = sql_alchemy_engine
    insert_assignments(engine, l_id)
    student_username = "e.noether"
    student = insert_student(engine, student_username, l_id)
    # Create a student submission and a user repo
    submission = create_user_submission_with_repo(engine, gitbase_dir, student, a_id, l_code)
    commit_hash = submission.commit_hash

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/{submission.id}/edit"

    with (
        patch(
            "grader_service.handlers.submissions.SubmissionEditHandler", new=SubmissionEditHandler
        ) as handler_mock,
        patch.object(SubmissionEditHandler, "gitbase", str(gitbase_dir)),
    ):
        handler_mock.application = MagicMock(spec=GraderServer)
        handler_mock.application.grader_service_dir = str(tmp_path)

        resp = await http_server_client.fetch(
            url,
            method="PUT",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps({}),
        )

    assert resp.code == HTTPStatus.OK
    submission_dict = json.loads(resp.body.decode())
    assert submission_dict["edited"] is True
    assert submission_dict["commit_hash"] == commit_hash
    assert submission_dict["user_display_name"] == student_username
    assert os.path.exists(gitbase_dir / l_code / str(a_id) / "edit" / str(submission_dict["id"]))


async def test_submission_cannot_edit_submission_created_by_instructor(
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
    tmp_path,
):
    l_id = 3  # default user has to be instructor
    a_id = 3

    # Set-up: As the instructor, create a new submission for a student
    engine = sql_alchemy_engine
    insert_assignments(engine, l_id)
    student_username = "e.noether"
    insert_student(engine, student_username, l_id)

    post_url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/"

    with (
        patch("subprocess.run"),
        patch.object(SubmissionHandler, "construct_git_dir", str(tmp_path)),
        patch("grader_service.handlers.submissions.chain", autospec=True),
    ):
        response = await http_server_client.fetch(
            post_url,
            method="POST",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(
                {"commit_hash": INSTRUCTOR_SUBMISSION_COMMIT_CASH, "username": student_username}
            ),
        )
    assert response.code == HTTPStatus.CREATED

    # Try to edit the submission created by the instructor - this should fail
    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/1/edit"

    with pytest.raises(
            HTTPClientError,
            match="This repo cannot be edited or reset, because it was created by instructor",
    ) as exc_info:
        await http_server_client.fetch(
            url,
            method="PUT",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps({}),
        )
    e = exc_info.value
    assert e.code == HTTPStatus.BAD_REQUEST


async def test_get_submissions_username(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
    default_user,
    default_admin,
):
    a_id = 1
    url = service_base_url + f"users/{default_user.name}/submissions"

    insert_submission(sql_alchemy_engine, a_id, default_user.name, default_user.id)
    insert_submission(sql_alchemy_engine, a_id, default_admin.name, default_admin.id)

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK
    submissions = json.loads(response.body.decode())
    assert isinstance(submissions, list)
    assert len(submissions) == 1
    assert submissions[0]["user_id"] == default_user.id
    Submission.from_dict(submissions[0])


async def test_get_submissions_username_student_from_another_student(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
    default_user,
    default_admin,
):
    a_id = 1
    url = service_base_url + f"users/{default_admin.name}/submissions"

    insert_submission(sql_alchemy_engine, a_id, default_user.name, default_user.id)
    insert_submission(sql_alchemy_engine, a_id, default_admin.name, default_admin.id)

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.FORBIDDEN


async def test_get_submissions_username_admin_from_another_student(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_admin_login,
    default_user,
    default_admin,
):
    a_id = 1
    url = service_base_url + f"users/{default_user.name}/submissions"

    insert_submission(sql_alchemy_engine, a_id, default_user.name, default_user.id)
    insert_submission(sql_alchemy_engine, a_id, default_admin.name, default_admin.id)

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK
    submissions = json.loads(response.body.decode())
    assert isinstance(submissions, list)
    assert len(submissions) == 1
    assert submissions[0]["user_id"] == default_user.id
    Submission.from_dict(submissions[0])


async def test_get_submissions_username_admin_user_not_found(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_admin_login,
    default_user,
    default_admin,
):
    a_id = 1
    username = "windows"
    url = service_base_url + f"users/{username}/submissions"

    insert_submission(sql_alchemy_engine, a_id, default_user.name, default_user.id)
    insert_submission(sql_alchemy_engine, a_id, default_admin.name, default_admin.id)

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND


async def test_get_submissions_username_format_csv(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    a_id = 1
    url = service_base_url + f"users/{default_user.name}/submissions?format=csv"
    await submission_test_setup(sql_alchemy_engine, default_user, a_id)

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK
    decoded_content = response.body.decode("utf-8")

    body_csv = csv.reader(decoded_content.splitlines(), delimiter=",")
    submissions = list(body_csv)
    # Delete column description
    submissions.pop(0)

    assert len(submissions) == 2
    assert submissions[0][4] == str(default_user.id)
    assert submissions[1][4] == str(default_user.id)
    assert submissions[0][5] == default_user.name
    assert submissions[1][5] == default_user.name


async def test_get_submissions_username_format_wrong(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
    default_user,
):
    url = service_base_url + f"users/{default_user.name}/submissions?format=abc"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.BAD_REQUEST


async def test_get_submissions_username_filter_wrong(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    url = service_base_url + f"users/{default_user.name}/submissions?filter=abc"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.BAD_REQUEST
