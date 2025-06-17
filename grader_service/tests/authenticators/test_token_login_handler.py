# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from grader_service.auth.token import JupyterHubTokenAuthenticator, TokenLoginHandler
from grader_service.server import GraderServer
import json

from pytest_tornasync.plugin import AsyncHTTPServerClient

# Imports are important otherwise they will not be found
from ..handlers.tornado_test_utils import *


@pytest.fixture
def token_authenticator():
    authenticator = JupyterHubTokenAuthenticator()
    authenticator.allow_all = True
    authenticator.post_auth_hook = lambda _, __, auth_model: auth_model
    yield authenticator


url = "/login"


async def test_login_handler(
    app: GraderServer,
    service_base_url,
    http_server_client: AsyncHTTPServerClient,
    default_token,
    default_roles,
    default_user_login,
    token_authenticator: JupyterHubTokenAuthenticator,
    sql_alchemy_sessionmaker,
    default_user,
):
    async_mock = AsyncMock()

    response_mock = MagicMock()

    response_mock.body = json.dumps({"name": default_user.name, "groups": ["lect1:test"]})

    async_mock.fetch = AsyncMock(return_value=response_mock)

    app.add_handlers(host_pattern=".*", host_handlers=token_authenticator.get_handlers("/"))
    app.authenticator = token_authenticator

    with patch.object(JupyterHubTokenAuthenticator, "http_client", new=async_mock):
        response = await http_server_client.fetch(
            url, method="POST", body=json.dumps({"token": default_token}), request_timeout=100000
        )

    assert response.code == 200
    grader_token = json.loads(response.body.decode())
    assert isinstance(grader_token, dict)


async def test_login_handler_with_no_user(
    app: GraderServer,
    service_base_url,
    http_server_client: AsyncHTTPServerClient,
    default_token,
    default_roles,
    default_user_login,
    token_authenticator: JupyterHubTokenAuthenticator,
    sql_alchemy_sessionmaker,
    default_user,
):
    user_mock = AsyncMock(return_value=None)

    app.add_handlers(host_pattern=".*", host_handlers=token_authenticator.get_handlers("/"))
    app.authenticator = token_authenticator

    with patch.object(TokenLoginHandler, "login_user", new=user_mock):
        response = await http_server_client.fetch(
            url,
            method="POST",
            body=json.dumps({"token": default_token}),
            request_timeout=100000,
            raise_error=False,
        )

    assert response.code == 404
