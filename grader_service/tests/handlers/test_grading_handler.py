# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.


import json
from unittest.mock import MagicMock, patch

import celery
import pytest
from tornado.httpclient import HTTPClientError

import grader_service
import grader_service.tests.conftest
from grader_service.api.models.submission import Submission
from grader_service.server import GraderServer

from .db_util import insert_assignments, insert_submission


async def test_auto_grading(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_user,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 3  # default user is instructor
    a_id = 3

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/grading/1/auto"

    engine = sql_alchemy_engine
    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user.name, default_user.id)

    with patch.object(
        grader_service.autograding.celery.app.CeleryApp, "instance", return_value=MagicMock()
    ):
        with patch.object(
            grader_service.autograding.celery.tasks.autograde_task, "delay", return_value=None
        ) as task_mock:
            response = await http_server_client.fetch(
                url, method="GET", headers={"Authorization": f"Token {default_token}"}
            )

    assert response.code == 202
    submission = Submission.from_dict(json.loads(response.body.decode()))
    assert submission.id == 1

    task_mock.assert_called()


async def test_auto_grading_wrong_assignment(
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

    a_id = 99
    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/grading/1/auto"

    with patch.object(
        grader_service.autograding.celery.app.CeleryApp, "instance", return_value=MagicMock()
    ):
        with patch.object(
            grader_service.autograding.celery.tasks.autograde_task, "delay", return_value=None
        ):
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
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    a_id = 1

    engine = sql_alchemy_engine
    insert_submission(engine, a_id, default_user.name, default_user.id)

    l_id = 99
    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/grading/1/auto"

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
    default_user,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 3  # default user is instructor
    a_id = 3

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/grading/1/feedback"

    engine = sql_alchemy_engine
    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user.name, default_user.id)

    with patch.object(
        grader_service.autograding.celery.app.CeleryApp, "instance", return_value=MagicMock()
    ):
        with patch.object(
            grader_service.autograding.celery.tasks.generate_feedback_task, "si", return_value=None
        ):
            with patch.object(
                grader_service.autograding.celery.tasks.lti_sync_task, "si", return_value=None
            ):
                with patch.object(celery, "chain", return_value=MagicMock) as chain_mock:
                    response = await http_server_client.fetch(
                        url, method="GET", headers={"Authorization": f"Token {default_token}"}
                    )
    assert response.code == 202
    submission = Submission.from_dict(json.loads(response.body.decode()))
    assert submission.id == 1

    chain_mock.assert_called()


async def test_feedback_wrong_assignment(
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

    a_id = 99
    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/grading/1/feedback"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == 404
