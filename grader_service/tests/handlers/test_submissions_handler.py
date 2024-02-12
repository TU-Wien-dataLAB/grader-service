# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
import csv
import subprocess
from datetime import datetime
from re import sub
import secrets
from unittest.mock import patch

import isodate
import pytest
from grader_service.server import GraderServer
import json
from grader_service.orm.assignment import Assignment as AssignmentORM
from grader_service.api.models.submission import Submission
from tornado.httpclient import HTTPClientError
from datetime import timezone
from .db_util import insert_submission, insert_take_part, _get_assignment

# Imports are important otherwise they will not be found
from .tornado_test_utils import *
from .db_util import insert_assignments
from ...api.models.assignment import Assignment
from ...handlers.base_handler import GraderBaseHandler
from ...handlers.submissions import SubmissionHandler
from ...orm import Role
from ...orm.takepart import Scope


async def submission_test_setup(sql_alchemy_db, http_server_client, default_user, default_token,
                                url: str, a_id: int):
    engine = sql_alchemy_db.engine
    insert_submission(engine, assignment_id=a_id, username=default_user["name"])
    insert_submission(engine, assignment_id=a_id, username=default_user["name"], with_properties=False)
    # should make no difference
    insert_submission(engine, assignment_id=a_id, username="user1")
    insert_submission(engine, assignment_id=a_id, username="user1", with_properties=False)

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    return response


@pytest.mark.parametrize("period,expected", [("P0D", 1.0), ("P1D", 0.5), ("P2D", 0.2), ("P3D", 0.1)])
def test_calculate_late_submission_scaling(period, expected):
    a = AssignmentORM()
    role = Role()
    role.role = Scope.student
    now = datetime.utcnow()
    a.duedate = now

    settings = {
        "late_submission": [{"period": "P1D", "scaling": 0.5},
                            {"period": "P2D", "scaling": 0.2},
                            {"period": "P3D", "scaling": 0.1}]
    }
    a.settings = json.dumps(settings)

    submission_ts = now - isodate.parse_duration("PT1S") + isodate.parse_duration(period)
    assert SubmissionHandler.calculate_late_submission_scaling(a, submission_ts, role) == expected


def test_calculate_late_submission_scaling_error():
    a = AssignmentORM()
    role = Role()
    role.role = Scope.student
    now = datetime.utcnow()
    a.duedate = now

    settings = {
        "late_submission": [{"period": "P1D", "scaling": 0.5}]
    }
    a.settings = json.dumps(settings)

    submission_ts = now + isodate.parse_duration("P1M")
    from tornado.web import HTTPError
    with pytest.raises(HTTPError):
        SubmissionHandler.calculate_late_submission_scaling(a, submission_ts, role)


async def test_get_submissions(
        app: GraderServer,
        service_base_url,
        http_server_client,
        jupyter_hub_mock_server,
        default_user,
        default_token,
        sql_alchemy_db,
):
    http_server = jupyter_hub_mock_server(default_user, default_token)
    app.auth_cls.hub_api_url = http_server.url_for("")[0:-1]

    a_id = 1
    url = service_base_url + f"/lectures/1/assignments/{a_id}/submissions/"
    response = await submission_test_setup(sql_alchemy_db,
                                           http_server_client,
                                           default_user,
                                           default_token,
                                           url,
                                           a_id)
    assert response.code == 200
    submissions = json.loads(response.body.decode())
    assert isinstance(submissions, list)
    assert len(submissions) == 2
    assert submissions[0]["username"] == "ubuntu"
    assert submissions[1]["username"] == "ubuntu"
    Submission.from_dict(submissions[0])


async def test_get_submissions_format_csv(
        app: GraderServer,
        service_base_url,
        http_server_client,
        jupyter_hub_mock_server,
        default_user,
        default_token,
        sql_alchemy_db,
):
    http_server = jupyter_hub_mock_server(default_user, default_token)
    app.auth_cls.hub_api_url = http_server.url_for("")[0:-1]

    a_id = 1
    url = service_base_url + f"/lectures/1/assignments/{a_id}/submissions/?format=csv"
    response = await submission_test_setup(sql_alchemy_db,
                                           http_server_client,
                                           default_user,
                                           default_token,
                                           url,
                                           a_id)
    assert response.code == 200
    decoded_content = response.body.decode('utf-8')

    body_csv = csv.reader(decoded_content.splitlines(), delimiter=',')
    submissions = list(body_csv)
    # Delete column description
    submissions.pop(0)

    assert len(submissions) == 2
    assert submissions[0][4] == "ubuntu"
    assert submissions[1][4] == "ubuntu"
    Submission.from_dict(submissions[0])


async def test_get_submissions_format_wrong(
        app: GraderServer,
        service_base_url,
        http_server_client,
        jupyter_hub_mock_server,
        default_user,
        default_token,
        sql_alchemy_db,
):
    http_server = jupyter_hub_mock_server(default_user, default_token)
    app.auth_cls.hub_api_url = http_server.url_for("")[0:-1]

    l_id = 1  # default user is student
    a_id = 1
    engine = sql_alchemy_db.engine

    url = service_base_url + f"/lectures/{l_id}/assignments/{a_id}/submissions/?format=abc"

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
        jupyter_hub_mock_server,
        default_user,
        default_token,
        sql_alchemy_db,
):
    http_server = jupyter_hub_mock_server(default_user, default_token)
    app.auth_cls.hub_api_url = http_server.url_for("")[0:-1]

    l_id = 1  # default user is student
    a_id = 1
    engine = sql_alchemy_db.engine

    url = service_base_url + f"/lectures/{l_id}/assignments/{a_id}/submissions/?filter=abc"

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
        jupyter_hub_mock_server,
        default_user,
        default_token,
        sql_alchemy_db,
):
    http_server = jupyter_hub_mock_server(default_user, default_token)
    app.auth_cls.hub_api_url = http_server.url_for("")[0:-1]

    l_id = 3
    a_id = 4
    engine = sql_alchemy_db.engine
    insert_assignments(engine, l_id)

    url = service_base_url + f"/lectures/{l_id}/assignments/{a_id}/submissions/?instructor-version=true"

    insert_submission(engine, assignment_id=a_id, username=default_user["name"])
    insert_submission(engine, assignment_id=a_id, username=default_user["name"], with_properties=False)
    insert_submission(engine, assignment_id=a_id, username="user1")
    insert_submission(engine, assignment_id=a_id, username="user1", with_properties=False)

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == 200
    submissions = json.loads(response.body.decode())
    assert isinstance(submissions, list)
    assert len(submissions) == 4
    user_submission = submissions[0:2]

    possible_users = {default_user["name"], "user1"}
    user_name = submissions[0]["username"]
    assert user_name in possible_users
    possible_users.remove(user_name)

    assert isinstance(user_submission, list)
    assert len(user_submission) == 2
    assert all([isinstance(s, dict) for s in user_submission])
    [Submission.from_dict(s) for s in user_submission]

    user_submission = submissions[2:4]

    user_name = user_submission[0]["username"]
    assert user_name in possible_users
    possible_users.remove(user_name)
    assert len(possible_users) == 0

    assert isinstance(user_submission, list)
    assert len(user_submission) == 2
    assert all([isinstance(s, dict) for s in user_submission])
    [Submission.from_dict(s) for s in user_submission]


async def test_get_submissions_instructor_version_unauthorized(
        app: GraderServer,
        service_base_url,
        http_server_client,
        jupyter_hub_mock_server,
        default_user,
        default_token,
        sql_alchemy_db,
):
    default_user["groups"] = ["20wle2:student", "21wle1:student", "22wle1:student"]
    http_server = jupyter_hub_mock_server(default_user, default_token)
    app.auth_cls.hub_api_url = http_server.url_for("")[0:-1]

    l_id = 1  # default user is student
    a_id = 1
    engine = sql_alchemy_db.engine

    url = service_base_url + f"/lectures/{l_id}/assignments/{a_id}/submissions/?instructor-version=true"

    insert_submission(engine, assignment_id=a_id, username=default_user["name"])
    insert_submission(engine, assignment_id=a_id, username=default_user["name"], with_properties=False)

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
        jupyter_hub_mock_server,
        default_user,
        default_token,
        sql_alchemy_db,
):
    http_server = jupyter_hub_mock_server(default_user, default_token)
    app.auth_cls.hub_api_url = http_server.url_for("")[0:-1]

    l_id = 3
    a_id = 4
    engine = sql_alchemy_db.engine
    insert_assignments(engine, l_id)

    url = service_base_url + f"/lectures/{l_id}/assignments/{a_id}/submissions/?instructor-version=true&filter=latest"

    insert_submission(engine, assignment_id=a_id, username=default_user["name"])
    insert_submission(engine, assignment_id=a_id, username=default_user["name"], with_properties=False)
    insert_submission(engine, assignment_id=a_id, username="user1")
    insert_submission(engine, assignment_id=a_id, username="user1", with_properties=False)

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == 200
    submissions = json.loads(response.body.decode())
    assert isinstance(submissions, list)
    assert len(submissions) == 2
    # Submissions of first user
    user_submission = submissions[0:1]

    possible_users = {default_user["name"], "user1"}
    user_name = user_submission[0]["username"]
    assert user_name in possible_users
    possible_users.remove(user_name)

    assert isinstance(user_submission, list)
    assert len(user_submission) == 1
    assert all([isinstance(s, dict) for s in user_submission])
    [Submission.from_dict(s) for s in user_submission]

    user_submission = submissions[1:2]

    user_name = user_submission[0]["username"]
    assert user_name in possible_users
    possible_users.remove(user_name)
    assert len(possible_users) == 0

    assert isinstance(user_submission, list)
    assert len(user_submission) == 1
    assert all([isinstance(s, dict) for s in user_submission])
    [Submission.from_dict(s) for s in user_submission]


async def test_get_submissions_best_instructor_version(
        app: GraderServer,
        service_base_url,
        http_server_client,
        jupyter_hub_mock_server,
        default_user,
        default_token,
        sql_alchemy_db,
):
    http_server = jupyter_hub_mock_server(default_user, default_token)
    app.auth_cls.hub_api_url = http_server.url_for("")[0:-1]

    l_id = 3
    a_id = 4
    engine = sql_alchemy_db.engine
    insert_assignments(engine, l_id)

    url = service_base_url + f"/lectures/{l_id}/assignments/{a_id}/submissions/?instructor-version=true&filter=best"

    insert_submission(engine, assignment_id=a_id, username=default_user["name"], feedback=True, score=3)
    insert_submission(engine, assignment_id=a_id, username=default_user["name"], feedback=False, with_properties=False)
    insert_submission(engine, assignment_id=a_id, username="user1", score=3)
    insert_submission(engine, assignment_id=a_id, username="user1", with_properties=False)

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == 200
    submissions = json.loads(response.body.decode())
    assert isinstance(submissions, list)
    assert len(submissions) == 2
    # Submissions of first user
    user_submission = submissions[0:1]

    possible_users = {default_user["name"], "user1"}
    user_name = user_submission[0]["username"]
    assert user_name in possible_users
    possible_users.remove(user_name)

    assert isinstance(user_submission, list)
    assert len(user_submission) == 1
    assert all([isinstance(s, dict) for s in user_submission])
    [Submission.from_dict(s) for s in user_submission]


async def test_get_submissions_lecture_assignment_missmatch(
        app: GraderServer,
        service_base_url,
        http_server_client,
        jupyter_hub_mock_server,
        default_user,
        default_token,
        sql_alchemy_db,
):
    http_server = jupyter_hub_mock_server(default_user, default_token)
    app.auth_cls.hub_api_url = http_server.url_for("")[0:-1]

    l_id = 3
    a_id = 1
    url = service_base_url + f"/lectures/{l_id}/assignments/{a_id}/submissions/"

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
        jupyter_hub_mock_server,
        default_user,
        default_token,
        sql_alchemy_db,
):
    http_server = jupyter_hub_mock_server(default_user, default_token)
    app.auth_cls.hub_api_url = http_server.url_for("")[0:-1]

    l_id = 1
    a_id = 99
    url = service_base_url + f"/lectures/{l_id}/assignments/{a_id}/submissions/"

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
        jupyter_hub_mock_server,
        default_user,
        default_token,
        sql_alchemy_db,
):
    http_server = jupyter_hub_mock_server(default_user, default_token)
    app.auth_cls.hub_api_url = http_server.url_for("")[0:-1]

    l_id = 3  # user has to be instructor
    a_id = 4
    engine = sql_alchemy_db.engine
    insert_assignments(engine, l_id)

    url = service_base_url + f"/lectures/{l_id}/assignments/{a_id}/submissions/1/"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"},
        )
    e = exc_info.value
    assert e.code == 404

    insert_submission(engine, a_id, default_user["name"])

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"},
    )
    assert response.code == 200
    submission_dict = json.loads(response.body.decode())
    Submission.from_dict(submission_dict)


async def test_get_submission_assignment_lecture_missmatch(
        app: GraderServer,
        service_base_url,
        http_server_client,
        jupyter_hub_mock_server,
        default_user,
        default_token,
        sql_alchemy_db,
):
    http_server = jupyter_hub_mock_server(default_user, default_token)
    app.auth_cls.hub_api_url = http_server.url_for("")[0:-1]

    l_id = 3  # user has to be instructor
    engine = sql_alchemy_db.engine
    insert_assignments(engine, l_id)

    a_id = 1  # assignment with a_id 1 is in l_id 1
    url = service_base_url + f"/lectures/{l_id}/assignments/{a_id}/submissions/1/"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"},
        )
    e = exc_info.value
    assert e.code == 404


async def test_get_submission_assignment_submission_missmatch(
        app: GraderServer,
        service_base_url,
        http_server_client,
        jupyter_hub_mock_server,
        default_user,
        default_token,
        sql_alchemy_db,
):
    http_server = jupyter_hub_mock_server(default_user, default_token)
    app.auth_cls.hub_api_url = http_server.url_for("")[0:-1]

    l_id = 3  # user has to be instructor
    a_id = 4
    engine = sql_alchemy_db.engine
    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user["name"])

    a_id = 1  # this assignment has no submissions
    url = service_base_url + f"/lectures/{l_id}/assignments/{a_id}/submissions/1/"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"},
        )
    e = exc_info.value
    assert e.code == 404


async def test_get_submission_wrong_submission(
        app: GraderServer,
        service_base_url,
        http_server_client,
        jupyter_hub_mock_server,
        default_user,
        default_token,
        sql_alchemy_db,
):
    http_server = jupyter_hub_mock_server(default_user, default_token)
    app.auth_cls.hub_api_url = http_server.url_for("")[0:-1]

    l_id = 3  # user has to be instructor
    a_id = 3
    engine = sql_alchemy_db.engine
    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user["name"])

    a_id = 1  # this assignment has no submissions
    url = service_base_url + f"/lectures/{l_id}/assignments/{a_id}/submissions/99/"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"},
        )
    e = exc_info.value
    assert e.code == 404


async def test_get_submission_unauthorized(
        app: GraderServer,
        service_base_url,
        http_server_client,
        jupyter_hub_mock_server,
        default_user,
        default_token,
):
    default_user["groups"] = ["20wle2:student", "21wle1:student", "22wle1:student"]
    http_server = jupyter_hub_mock_server(default_user, default_token)
    app.auth_cls.hub_api_url = http_server.url_for("")[0:-1]

    l_id = 1  # user is student
    a_id = 1

    url = service_base_url + f"/lectures/{l_id}/assignments/{a_id}/submissions/1/"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"},
        )
    e = exc_info.value
    assert e.code == 404


async def test_put_submission(
        app: GraderServer,
        service_base_url,
        http_server_client,
        jupyter_hub_mock_server,
        default_user,
        default_token,
        sql_alchemy_db,
):
    http_server = jupyter_hub_mock_server(default_user, default_token)
    app.auth_cls.hub_api_url = http_server.url_for("")[0:-1]

    l_id = 3  # default user is student
    a_id = 4

    url = service_base_url + f"/lectures/{l_id}/assignments/{a_id}/submissions/1/"

    engine = sql_alchemy_db.engine
    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user["name"])

    pre_submission = Submission(id=-1, submitted_at=None, commit_hash=secrets.token_hex(20),
                                auto_status="automatically_graded", manual_status="manually_graded")
    response = await http_server_client.fetch(
        url, method="PUT", headers={"Authorization": f"Token {default_token}"},
        body=json.dumps(pre_submission.to_dict()),
    )
    assert response.code == 200
    submission_dict = json.loads(response.body.decode())
    submission = Submission.from_dict(submission_dict)
    assert submission.id == 1
    assert submission.auto_status == pre_submission.auto_status
    assert submission.manual_status == pre_submission.manual_status
    assert submission.commit_hash != pre_submission.commit_hash  # commit hash cannot be changed
    assert not submission.feedback_available
    # assert submission.submitted_at.strftime("%Y-%m-%dT%H:%M:%S.%f")[0:-3] + "Z" == pre_submission.submitted_at
    assert submission.score is None


async def test_put_submission_lecture_assignment_missmatch(
        app: GraderServer,
        service_base_url,
        http_server_client,
        jupyter_hub_mock_server,
        default_user,
        default_token,
        sql_alchemy_db,
):
    http_server = jupyter_hub_mock_server(default_user, default_token)
    app.auth_cls.hub_api_url = http_server.url_for("")[0:-1]

    l_id = 3
    a_id = 1
    url = service_base_url + f"/lectures/{l_id}/assignments/{a_id}/submissions/1"

    engine = sql_alchemy_db.engine
    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user["name"])

    now = datetime.utcnow().isoformat("T", "milliseconds") + "Z"
    pre_submission = Submission(id=-1, submitted_at=now, commit_hash=secrets.token_hex(20),
                                auto_status="automatically_graded", manual_status="manually_graded")
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="PUT", headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(pre_submission.to_dict()),
        )
    e = exc_info.value
    assert e.code == 404


async def test_put_submission_assignment_submission_missmatch(
        app: GraderServer,
        service_base_url,
        http_server_client,
        jupyter_hub_mock_server,
        default_user,
        default_token,
        sql_alchemy_db,
):
    http_server = jupyter_hub_mock_server(default_user, default_token)
    app.auth_cls.hub_api_url = http_server.url_for("")[0:-1]

    l_id = 3  # user has to be instructor
    a_id = 3
    engine = sql_alchemy_db.engine
    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user["name"])

    a_id = 1  # this assignment has no submissions
    url = service_base_url + f"/lectures/{l_id}/assignments/{a_id}/submissions/1/"

    now = datetime.utcnow().isoformat("T", "milliseconds") + "Z"
    pre_submission = Submission(id=-1, submitted_at=now, commit_hash=secrets.token_hex(20),
                                auto_status="automatically_graded", manual_status="manually_graded")
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="PUT", headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(pre_submission.to_dict()),
        )
    e = exc_info.value
    assert e.code == 404


async def test_put_submission_wrong_submission(
        app: GraderServer,
        service_base_url,
        http_server_client,
        jupyter_hub_mock_server,
        default_user,
        default_token,
        sql_alchemy_db,
):
    http_server = jupyter_hub_mock_server(default_user, default_token)
    app.auth_cls.hub_api_url = http_server.url_for("")[0:-1]

    l_id = 3  # user has to be instructor
    a_id = 3
    engine = sql_alchemy_db.engine
    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user["name"])

    a_id = 1  # this assignment has no submissions
    url = service_base_url + f"/lectures/{l_id}/assignments/{a_id}/submissions/99/"

    now = datetime.utcnow().isoformat("T", "milliseconds") + "Z"
    pre_submission = Submission(id=-1, submitted_at=now, commit_hash=secrets.token_hex(20),
                                auto_status="automatically_graded", manual_status="manually_graded")
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="PUT", headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(pre_submission.to_dict()),
        )
    e = exc_info.value
    assert e.code == 404


async def test_post_submission(
        app: GraderServer,
        service_base_url,
        http_server_client,
        jupyter_hub_mock_server,
        default_user,
        default_token,
        sql_alchemy_db,
        tmp_path
):
    http_server = jupyter_hub_mock_server(default_user, default_token)
    app.auth_cls.hub_api_url = http_server.url_for("")[0:-1]

    l_id = 3  # user has to be instructor
    a_id = 3
    engine = sql_alchemy_db.engine
    insert_assignments(engine, l_id)

    url = service_base_url + f"/lectures/{l_id}/assignments/{a_id}/submissions/"

    now = datetime.utcnow().isoformat("T", "milliseconds") + "Z"
    pre_submission = Submission(id=-1, submitted_at=now, commit_hash=secrets.token_hex(20),
                                auto_status="automatically_graded", manual_status="manually_graded")

    with patch.object(subprocess, "run", return_value=None):
        with patch.object(GraderBaseHandler, "construct_git_dir", return_value=str(tmp_path)):
            response = await http_server_client.fetch(
                url, method="POST", headers={"Authorization": f"Token {default_token}"},
                body=json.dumps(pre_submission.to_dict()),
            )

    assert response.code == 201


async def test_post_submission_git_repo_not_found(
        app: GraderServer,
        service_base_url,
        http_server_client,
        jupyter_hub_mock_server,
        default_user,
        default_token,
        sql_alchemy_db,
):
    http_server = jupyter_hub_mock_server(default_user, default_token)
    app.auth_cls.hub_api_url = http_server.url_for("")[0:-1]

    l_id = 3  # user has to be instructor
    a_id = 3
    engine = sql_alchemy_db.engine
    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user["name"])

    url = service_base_url + f"/lectures/{l_id}/assignments/{a_id}/submissions/"

    now = datetime.utcnow().isoformat("T", "milliseconds") + "Z"
    pre_submission = Submission(id=-1, submitted_at=now, commit_hash=secrets.token_hex(20),
                                auto_status="automatically_graded", manual_status="manually_graded")
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="POST", headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(pre_submission.to_dict()),
        )
    e = exc_info.value
    assert e.code == 404


async def test_post_submission_commit_hash_not_found(
        app: GraderServer,
        service_base_url,
        http_server_client,
        jupyter_hub_mock_server,
        default_user,
        default_token,
        sql_alchemy_db,
):
    http_server = jupyter_hub_mock_server(default_user, default_token)
    app.auth_cls.hub_api_url = http_server.url_for("")[0:-1]

    l_id = 3  # user has to be instructor
    a_id = 3
    engine = sql_alchemy_db.engine
    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user["name"])

    url = service_base_url + f"/lectures/{l_id}/assignments/{a_id}/submissions/"

    pre_submission = {"value": "10"}
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="POST", headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(pre_submission),
        )
    e = exc_info.value
    assert e.code == 400


async def test_submission_properties(
        app: GraderServer,
        service_base_url,
        http_server_client,
        jupyter_hub_mock_server,
        default_user,
        default_token,
        sql_alchemy_db,
):
    http_server = jupyter_hub_mock_server(default_user, default_token)
    app.auth_cls.hub_api_url = http_server.url_for("")[0:-1]

    l_id = 3  # default user is student
    a_id = 4

    url = service_base_url + f"/lectures/{l_id}/assignments/{a_id}/submissions/1/properties"

    engine = sql_alchemy_db.engine
    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user["name"])

    prop = {"notebooks": {}}
    put_response = await http_server_client.fetch(
        url,
        method="PUT",
        headers={"Authorization": f"Token {default_token}"},
        body=json.dumps(prop),
    )
    assert put_response.code == 200
    get_response = await http_server_client.fetch(
        url,
        method="GET",
        headers={"Authorization": f"Token {default_token}"},
    )
    assert get_response.code == 200
    assignment_props = json.loads(get_response.body.decode())
    assert assignment_props == prop


async def test_submission_properties_not_correct(
        app: GraderServer,
        service_base_url,
        http_server_client,
        jupyter_hub_mock_server,
        default_user,
        default_token,
        sql_alchemy_db,
):
    http_server = jupyter_hub_mock_server(default_user, default_token)
    app.auth_cls.hub_api_url = http_server.url_for("")[0:-1]

    l_id = 3  # default user is student
    a_id = 4

    url = service_base_url + f"/lectures/{l_id}/assignments/{a_id}/submissions/1/properties"

    engine = sql_alchemy_db.engine
    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user["name"])

    prop = "{}"
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="PUT",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(prop)
        )
    e = exc_info.value
    assert e.code == 400


async def test_submission_properties_not_found(
        app: GraderServer,
        service_base_url,
        http_server_client,
        jupyter_hub_mock_server,
        default_user,
        default_token,
        sql_alchemy_db,
):
    http_server = jupyter_hub_mock_server(default_user, default_token)
    app.auth_cls.hub_api_url = http_server.url_for("")[0:-1]

    l_id = 3  # default user is student
    a_id = 4

    url = service_base_url + f"/lectures/{l_id}/assignments/{a_id}/submissions/1/properties"

    engine = sql_alchemy_db.engine
    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user["name"])
    insert_submission(engine, a_id, default_user["name"])
    insert_submission(engine, a_id, default_user["name"])

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="GET",
            headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == 404


async def test_submission_properties_lecture_assignment_missmatch(
        app: GraderServer,
        service_base_url,
        http_server_client,
        jupyter_hub_mock_server,
        default_user,
        default_token,
        sql_alchemy_db,
):
    http_server = jupyter_hub_mock_server(default_user, default_token)
    app.auth_cls.hub_api_url = http_server.url_for("")[0:-1]

    l_id = 3
    a_id = 1
    engine = sql_alchemy_db.engine
    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user["name"])

    url = service_base_url + f"/lectures/{l_id}/assignments/{a_id}/submissions/1/properties"

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
            url,
            method="GET",
            headers={"Authorization": f"Token {default_token}"},
        )
    e = exc_info.value
    assert e.code == 404


async def test_submission_properties_assignment_submission_missmatch(
        app: GraderServer,
        service_base_url,
        http_server_client,
        jupyter_hub_mock_server,
        default_user,
        default_token,
        sql_alchemy_db,
):
    http_server = jupyter_hub_mock_server(default_user, default_token)
    app.auth_cls.hub_api_url = http_server.url_for("")[0:-1]

    l_id = 3  # user has to be instructor
    a_id = 3
    engine = sql_alchemy_db.engine
    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user["name"])

    a_id = 1  # this assignment has no submissions
    url = service_base_url + f"/lectures/{l_id}/assignments/{a_id}/submissions/1/properties"

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
            url,
            method="GET",
            headers={"Authorization": f"Token {default_token}"},
        )
    e = exc_info.value
    assert e.code == 404


async def test_submission_properties_wrong_submission(
        app: GraderServer,
        service_base_url,
        http_server_client,
        jupyter_hub_mock_server,
        default_user,
        default_token,
        sql_alchemy_db,
):
    http_server = jupyter_hub_mock_server(default_user, default_token)
    app.auth_cls.hub_api_url = http_server.url_for("")[0:-1]

    l_id = 3  # user has to be instructor
    a_id = 3
    engine = sql_alchemy_db.engine
    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user["name"])

    a_id = 1  # this assignment has no submissions
    url = service_base_url + f"/lectures/{l_id}/assignments/{a_id}/submissions/99/properties"

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
            url,
            method="GET",
            headers={"Authorization": f"Token {default_token}"},
        )
    e = exc_info.value
    assert e.code == 404


async def test_submission_properties_not_found(
        app: GraderServer,
        service_base_url,
        http_server_client,
        jupyter_hub_mock_server,
        default_user,
        default_token,
        sql_alchemy_db,
):
    http_server = jupyter_hub_mock_server(default_user, default_token)
    app.auth_cls.hub_api_url = http_server.url_for("")[0:-1]

    l_id = 3  # user has to be instructor
    a_id = 3
    engine = sql_alchemy_db.engine
    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user["name"], with_properties=False)

    a_id = 1  # this assignment has no submissions
    url = service_base_url + f"/lectures/{l_id}/assignments/{a_id}/submissions/1/properties"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="GET",
            headers={"Authorization": f"Token {default_token}"},
        )
    e = exc_info.value
    assert e.code == 404


async def test_max_submissions_assignment(
        app: GraderServer,
        service_base_url,
        http_server_client,
        jupyter_hub_mock_server,
        default_user,
        default_token,
        sql_alchemy_db,
        tmp_path
):
    default_user["groups"] = ["20wle2:student", "21wle1:student", "22wle1:student"]
    http_server = jupyter_hub_mock_server(default_user, default_token)
    app.auth_cls.hub_api_url = http_server.url_for("")[0:-1]

    l_id = 3
    a_id = 3

    session = sql_alchemy_db.sessionmaker()
    assignment_orm = _get_assignment("pytest", l_id, "2055-06-06 23:59:00.000", 20, "released")
    assignment_orm.max_submissions = 1
    assignment_orm.automatic_grading = "unassisted"
    session.add(assignment_orm)
    session.commit()

    assert assignment_orm.id == 3

    url = service_base_url + f"/lectures/{l_id}/assignments/{a_id}/submissions/"

    now = datetime.utcnow().isoformat("T", "milliseconds") + "Z"
    pre_submission = Submission(id=-1, submitted_at=now, commit_hash=secrets.token_hex(20),
                                auto_status="automatically_graded", manual_status="manually_graded")

    with patch.object(subprocess, "run", return_value=None):
        with patch.object(GraderBaseHandler, "construct_git_dir", return_value=str(tmp_path)):
            response = await http_server_client.fetch(
                url, method="POST", headers={"Authorization": f"Token {default_token}"},
                body=json.dumps(pre_submission.to_dict()),
            )
    assert response.code == 201

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="POST", headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(pre_submission.to_dict()),
        )

    e = exc_info.value
    assert e.code == 409
