# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
import csv
import json
import secrets
from datetime import datetime, timezone
from http import HTTPStatus

import isodate
import pytest
from sqlalchemy.orm import sessionmaker
from tornado.httpclient import HTTPClientError

from grader_service.api.models.submission import Submission
from grader_service.handlers.submissions import SubmissionHandler
from grader_service.orm import Assignment as AssignmentORM
from grader_service.orm import Role
from grader_service.orm import Submission as SubmissionORM
from grader_service.orm.base import DeleteState
from grader_service.orm.submission import AutoStatus, FeedbackStatus, ManualStatus
from grader_service.orm.takepart import Scope
from grader_service.server import GraderServer

from .db_util import insert_assignments, insert_student, insert_submission


async def submission_test_setup(engine, default_user, a_id: int):
    insert_submission(engine, a_id, default_user.name, default_user.id)
    insert_submission(engine, a_id, default_user.name, default_user.id, with_properties=False)
    # should make no difference
    insert_submission(engine, a_id, "user1", 2137)
    insert_submission(engine, a_id, "user1", 2137, with_properties=False)


async def test_get_submission_unauthorized(
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
    insert_submission(sql_alchemy_engine, a_id, default_user.name, default_user.id)

    url = service_base_url + f"lectures/{l_id}/submissions/"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == 403


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
    assert response.code == 200
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
    assert response.code == 200
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
    assert e.code == 400


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
    assert e.code == 400


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
    assert response.code == 200
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

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == 403


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
    assert response.code == 200
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
        assignment_id=a_id,
        username=default_user.name,
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
    assert response.code == 200
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
    assert e.code == 404


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
    assert e.code == 404


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
    assert e.code == 404

    insert_submission(engine, a_id, default_user.name, default_user.id)

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == 200
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
    assert e.code == 404


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

    a_id = 1  # this assignment has no submissions
    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/1/"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == 404


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

    a_id = 1  # this assignment has no submissions
    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/99/"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == 404


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
    assert response.code == 200
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
    assert e.code == 404


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
    assert e.code == 404


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
    assert e.code == 404


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


async def test_delete_submission_from_another_student_fails(
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
    # The submission does NOT belong to the default user:
    insert_submission(sql_alchemy_engine, a_id, "other_student")

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/1/"
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND


async def test_delete_submission_with_feedback_fails(
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
    insert_submission(
        sql_alchemy_engine, a_id, default_user.name, feedback=FeedbackStatus.GENERATED
    )

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/1/"

    with pytest.raises(
        HTTPClientError, match="Only submissions without feedback can be deleted."
    ) as exc_info:
        await http_server_client.fetch(
            url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.FORBIDDEN


async def test_delete_submission_after_deadline_fails(
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

    session = sessionmaker(sql_alchemy_engine)()
    assign = session.query(AssignmentORM).get(1)
    assign.settings = {"deadline": datetime(1999, 6, 6, tzinfo=timezone.utc)}
    session.commit()
    session.flush()

    insert_submission(sql_alchemy_engine, a_id, default_user.name)

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/1/"
    with pytest.raises(
        HTTPClientError, match="Submission can't be deleted, due date of assigment has passed."
    ) as exc_info:
        await http_server_client.fetch(
            url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.FORBIDDEN


async def test_delete_submission_twice_fails(
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
            url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND


# FIXME: does not work because CeleryApp is never initialised during test and is missing config_file
# async def test_post_submission(
#         app: GraderServer,
#         service_base_url,
#         http_server_client,
#         default_user,
#         default_token,
#         sql_alchemy_engine,
#         tmp_path,
#         default_roles,
#         default_user_login,
# ):
#     l_id = 3  # user has to be instructor
#     a_id = 3
#     engine = sql_alchemy_engine
#     insert_assignments(engine, l_id)

#     url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/"

#     now = datetime.now(timezone.utc).isoformat("T", "milliseconds")
#     pre_submission = Submission(id=-1, submitted_at=now, commit_hash=secrets.token_hex(20),
#         auto_status=AutoStatus.AUTOMATICALLY_GRADED,
#         manual_status=ManualStatus.MANUALLY_GRADED,
#         feedback_status=FeedbackStatus.NOT_GENERATED,
#     )

#     with patch.object(subprocess, "run", return_value=None):
#         with patch.object(GraderBaseHandler, "construct_git_dir", return_value=str(tmp_path)):
#             response = await http_server_client.fetch(
#                 url, method="POST", headers={"Authorization": f"Token {default_token}"},
#                 body=json.dumps(pre_submission.to_dict()),
#             )

#     assert response.code == 201


async def test_post_submission_git_repo_not_found(
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

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="POST",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps({"commit_hash": secrets.token_hex(20)}),
        )
    e = exc_info.value
    assert e.code == 422
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
    assert e.code == 400
    assert e.message == "Commit hash not found in body"


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
    assert put_response.code == 200
    get_response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert get_response.code == 200
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
    assert e.code == 400
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
    assert e.code == 404

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == 404


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
    assert e.code == 404

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == 404


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
    assert e.code == 404
    assert e.message == f"Submission with id {sub_id} was not found"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == 404
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
    assert e.code == 404
    assert e.message == "Properties of submission were not found"


# FIXME: does not work because CeleryApp is never initialised during test and is missing config_file
# async def test_max_submissions_assignment(
#         app: GraderServer,
#         service_base_url,
#         http_server_client,
#         default_user,
#         default_token,
#         sql_alchemy_engine,
#         sql_alchemy_sessionmaker,
#         tmp_path,
#         default_roles,
#         default_user_login,
# ):
#     l_id = 1
#     a_id = 3

#     session = sql_alchemy_sessionmaker()

#     assignment_orm = _get_assignment("pytest", l_id, 20, "released", AssignmentSettings(deadline=datetime.now(tz=timezone.utc) + timedelta(weeks=2)))
#     assignment_orm.settings.max_submissions = 1
#     assignment_orm.settings.autograde_type = "unassisted"
#     session.add(assignment_orm)
#     session.commit()

#     assert assignment_orm.id == 3

#     url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/submissions/"

#     now = str(datetime.now(timezone.utc))
#     pre_submission = Submission(id=-1, submitted_at=now, commit_hash=secrets.token_hex(20),
#         auto_status=AutoStatus.AUTOMATICALLY_GRADED,
#         manual_status=ManualStatus.MANUALLY_GRADED
#     )

#     with patch.object(subprocess, "run", return_value=None):
#         with patch.object(GraderBaseHandler, "construct_git_dir", return_value=str(tmp_path)):
#             response = await http_server_client.fetch(
#                 url, method="POST", headers={"Authorization": f"Token {default_token}"},
#                 body=json.dumps(pre_submission.to_dict()),
#             )
#     assert response.code == 201

#     with pytest.raises(HTTPClientError) as exc_info:
#         await http_server_client.fetch(
#             url, method="POST", headers={"Authorization": f"Token {default_token}"},
#             body=json.dumps(pre_submission.to_dict()),
#         )

#     e = exc_info.value
#     assert e.code == 409
