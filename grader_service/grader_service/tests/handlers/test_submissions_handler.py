# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

from datetime import datetime
from re import sub
import secrets
import pytest
from grader_service.server import GraderServer
import json
from grader_service.api.models.user import User
from grader_service.api.models.submission import Submission
from tornado.httpclient import HTTPClientError
from datetime import timezone
from .db_util import insert_submission, insert_take_part

# Imports are important otherwise they will not be found
from .tornado_test_utils import *
from .db_util import insert_assignments


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
    app.hub_api_url = http_server.url_for("")[0:-1]

    a_id = 1
    url = service_base_url + f"/lectures/1/assignments/{a_id}/submissions/"

    engine = sql_alchemy_db.engine
    insert_submission(engine, assignment_id=a_id, username=default_user["name"])
    insert_submission(engine, assignment_id=a_id, username=default_user["name"])
    # should make no difference
    insert_submission(engine, assignment_id=a_id, username="user1")
    insert_submission(engine, assignment_id=a_id, username="user1")

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == 200
    submissions = json.loads(response.body.decode())
    assert isinstance(submissions, list)
    assert len(submissions) == 2
    assert submissions[0]["username"] == "ubuntu"
    assert submissions[1]["username"] == "ubuntu"
    Submission.from_dict(submissions[0])


async def test_get_submissions_latest(
    app: GraderServer,
    service_base_url,
    http_server_client,
    jupyter_hub_mock_server,
    default_user,
    default_token,
    sql_alchemy_db,
):  
    http_server = jupyter_hub_mock_server(default_user, default_token)
    app.hub_api_url = http_server.url_for("")[0:-1]

    a_id = 1
    url = service_base_url + f"/lectures/1/assignments/{a_id}/submissions/?filter=latest"

    engine = sql_alchemy_db.engine
    insert_submission(engine, assignment_id=a_id, username=default_user["name"])
    insert_submission(engine, assignment_id=a_id, username=default_user["name"])
    # should make no difference
    insert_submission(engine, assignment_id=a_id, username="user1")
    insert_submission(engine, assignment_id=a_id, username="user1")

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == 200
    submissions = json.loads(response.body.decode())
    assert isinstance(submissions, list)
    assert len(submissions) == 1
    assert submissions[0]["username"] == "ubuntu"

    submissions_list = submissions
    assert isinstance(submissions_list, list)
    assert isinstance(submissions_list[0], dict)
    Submission.from_dict(submissions_list[0])


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
    app.hub_api_url = http_server.url_for("")[0:-1]

    l_id = 3
    a_id = 4
    engine = sql_alchemy_db.engine
    insert_assignments(engine, l_id)

    url = service_base_url + f"/lectures/{l_id}/assignments/{a_id}/submissions/?instructor-version=true"

    insert_submission(engine, assignment_id=a_id, username=default_user["name"])
    insert_submission(engine, assignment_id=a_id, username=default_user["name"])
    insert_submission(engine, assignment_id=a_id, username="user1")
    insert_submission(engine, assignment_id=a_id, username="user1")

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
    app.hub_api_url = http_server.url_for("")[0:-1]

    l_id = 1 # default user is student
    a_id = 1
    engine = sql_alchemy_db.engine

    url = service_base_url + f"/lectures/{l_id}/assignments/{a_id}/submissions/?instructor-version=true"

    insert_submission(engine, assignment_id=a_id, username=default_user["name"])
    insert_submission(engine, assignment_id=a_id, username=default_user["name"])

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
    app.hub_api_url = http_server.url_for("")[0:-1]

    l_id = 3
    a_id = 4
    engine = sql_alchemy_db.engine
    insert_assignments(engine, l_id)

    url = service_base_url + f"/lectures/{l_id}/assignments/{a_id}/submissions/?instructor-version=true&filter=latest"

    insert_submission(engine, assignment_id=a_id, username=default_user["name"])
    insert_submission(engine, assignment_id=a_id, username=default_user["name"])
    insert_submission(engine, assignment_id=a_id, username="user1")
    insert_submission(engine, assignment_id=a_id, username="user1")

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
    app.hub_api_url = http_server.url_for("")[0:-1]

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
    app.hub_api_url = http_server.url_for("")[0:-1]

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
    app.hub_api_url = http_server.url_for("")[0:-1]

    l_id = 3 # user has to be instructor
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
    app.hub_api_url = http_server.url_for("")[0:-1]

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
    app.hub_api_url = http_server.url_for("")[0:-1]

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
    app.hub_api_url = http_server.url_for("")[0:-1]

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
    app.hub_api_url = http_server.url_for("")[0:-1]

    l_id = 1  # user is student
    a_id = 1

    url = service_base_url + f"/lectures/{l_id}/assignments/{a_id}/submissions/1/"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"},
        )
    e = exc_info.value
    assert e.code == 403


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
    app.hub_api_url = http_server.url_for("")[0:-1]

    l_id = 3 # default user is student
    a_id = 4

    url = service_base_url + f"/lectures/{l_id}/assignments/{a_id}/submissions/1/"

    engine = sql_alchemy_db.engine
    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user["name"])

    pre_submission = Submission(id=-1, submitted_at=None, commit_hash=secrets.token_hex(20), auto_status="automatically_graded", manual_status="manually_graded")
    response = await http_server_client.fetch(
        url, method="PUT", headers={"Authorization": f"Token {default_token}"}, body=json.dumps(pre_submission.to_dict()),
    )
    assert response.code == 200
    submission_dict = json.loads(response.body.decode())
    submission = Submission.from_dict(submission_dict)
    assert submission.id == 1
    assert submission.auto_status == pre_submission.auto_status
    assert submission.manual_status == pre_submission.manual_status
    assert submission.commit_hash != pre_submission.commit_hash # commit hash cannot be changed
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
    app.hub_api_url = http_server.url_for("")[0:-1]

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
    app.hub_api_url = http_server.url_for("")[0:-1]

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
    app.hub_api_url = http_server.url_for("")[0:-1]

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
    app.hub_api_url = http_server.url_for("")[0:-1]

    l_id = 3 # default user is student
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
    app.hub_api_url = http_server.url_for("")[0:-1]

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
    app.hub_api_url = http_server.url_for("")[0:-1]

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
    app.hub_api_url = http_server.url_for("")[0:-1]

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
    app.hub_api_url = http_server.url_for("")[0:-1]

    l_id = 3  # user has to be instructor
    a_id = 3
    engine = sql_alchemy_db.engine
    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user["name"])

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

