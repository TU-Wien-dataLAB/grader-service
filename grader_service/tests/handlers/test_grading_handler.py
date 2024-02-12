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
from grader_service.api.models.submission import Submission
from tornado.httpclient import HTTPClientError
from datetime import timezone
from .db_util import insert_submission
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from grader_service.autograding.local_grader import LocalAutogradeExecutor
from grader_service.autograding.local_feedback import GenerateFeedbackExecutor

# Imports are important otherwise they will not be found
from .db_util import insert_assignments
from .tornado_test_utils import *
from grader_service.autograding.grader_executor import GraderExecutor


async def test_auto_grading(
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

    l_id = 3 # default user is student
    a_id = 4

    url = service_base_url + f"/lectures/{l_id}/assignments/{a_id}/grading/1/auto"

    engine = sql_alchemy_db.engine
    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user["name"])

    with patch.object(LocalAutogradeExecutor, "start", return_value=None) as start_mock:
        response = await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
        assert response.code == 202
        submission = Submission.from_dict(json.loads(response.body.decode()))
        assert submission.id == 1

    start_mock.assert_called()


async def test_auto_grading_wrong_assignment(
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

    l_id = 3 # default user is student
    a_id = 3

    engine = sql_alchemy_db.engine
    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user["name"])

    a_id = 99
    url = service_base_url + f"/lectures/{l_id}/assignments/{a_id}/grading/1/auto"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == 404


async def test_auto_grading_wrong_lecture(
    app: GraderServer,
    service_base_url,
    http_server_client,
    jupyter_hub_mock_server,
    default_user,
    default_token,
    sql_alchemy_db,
):
    default_user["groups"] = ["20wle2:instructor", "21wle1:instructor", "22wle1:instructor"]
    http_server = jupyter_hub_mock_server(default_user, default_token)
    app.auth_cls.hub_api_url = http_server.url_for("")[0:-1]

    l_id = 3 # default user is student
    a_id = 3

    engine = sql_alchemy_db.engine
    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user["name"])

    l_id = 99
    # default user now instructor -> passes authorization for handler
    url = service_base_url + f"/lectures/{l_id}/assignments/{a_id}/grading/1/auto"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == 403


async def test_feedback(
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

    l_id = 3 # default user is student
    a_id = 4

    url = service_base_url + f"/lectures/{l_id}/assignments/{a_id}/grading/1/feedback"

    engine = sql_alchemy_db.engine
    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user["name"])

    with patch.object(GenerateFeedbackExecutor, "start", return_value=None) as start_mock:
        with patch.object(GraderExecutor, "submit", return_value=None) as submit_mock:
            response = await http_server_client.fetch(
                url, method="GET", headers={"Authorization": f"Token {default_token}"}
            )
            assert response.code == 202
            submission = Submission.from_dict(json.loads(response.body.decode()))
            assert submission.id == 1

    submit_mock.assert_called()


async def test_feedback_wrong_assignment(
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

    l_id = 3 # default user is student
    a_id = 3

    engine = sql_alchemy_db.engine
    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user["name"])

    a_id = 99
    url = service_base_url + f"/lectures/{l_id}/assignments/{a_id}/grading/1/feedback"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == 404

