from unittest.mock import MagicMock, patch

import pytest

from grader_service.auth.dummy import DummyAuthenticator
from grader_service.auth.login import LoginHandler
from grader_service.server import GraderServer

from pytest_tornasync.plugin import AsyncHTTPServerClient

# Imports are important otherwise they will not be found
from ..handlers.tornado_test_utils import *


@pytest.fixture
def dummy_authenticator():
    authenticator = DummyAuthenticator()
    authenticator.allow_all = True
    yield authenticator


async def test_dummy_authenticator_with_global_password(
    app: GraderServer,
    service_base_url,
    http_server_client: AsyncHTTPServerClient,
    default_token,
    dummy_authenticator: DummyAuthenticator,
    default_roles,
    default_user_login,
    sql_alchemy_sessionmaker,
    default_user,
):
    app.add_handlers(host_pattern=".*", host_handlers=dummy_authenticator.get_handlers("/"))
    app.authenticator = dummy_authenticator

    with patch.object(DummyAuthenticator, "password", new="password"):
        response = await http_server_client.fetch(
            "/login",
            method="POST",
            body=f"username={default_user.name}&password=password",
            follow_redirects=False,
            raise_error=False,
        )

    assert response.code == 302


async def test_login_handler_get_method(
    app: GraderServer,
    service_base_url,
    http_server_client: AsyncHTTPServerClient,
    default_token,
    dummy_authenticator: DummyAuthenticator,
    default_roles,
    default_user_login,
    sql_alchemy_sessionmaker,
    default_user,
):
    app.add_handlers(host_pattern=".*", host_handlers=dummy_authenticator.get_handlers("/"))
    app.authenticator = dummy_authenticator

    with patch.object(LoginHandler, "redirect", new=MagicMock()):
        response = await http_server_client.fetch("/login", method="GET", follow_redirects=False)

    assert response.code == 200


async def test_login_handler_post_method(
    app: GraderServer,
    service_base_url,
    http_server_client: AsyncHTTPServerClient,
    default_token,
    dummy_authenticator: DummyAuthenticator,
    default_roles,
    default_user_login,
    sql_alchemy_sessionmaker,
    default_user,
):
    app.add_handlers(host_pattern=".*", host_handlers=dummy_authenticator.get_handlers("/"))
    app.authenticator = dummy_authenticator

    response = await http_server_client.fetch(
        "/login",
        method="POST",
        body=f"username={default_user.name}",
        follow_redirects=False,
        raise_error=False,
    )

    assert response.code == 302


async def test_login_handler_post_method_with_no_user(
    app: GraderServer,
    service_base_url,
    http_server_client: AsyncHTTPServerClient,
    default_token,
    dummy_authenticator: DummyAuthenticator,
    default_roles,
    default_user_login,
    sql_alchemy_sessionmaker,
    default_user,
):
    app.add_handlers(host_pattern=".*", host_handlers=dummy_authenticator.get_handlers("/"))
    app.authenticator = dummy_authenticator

    response = await http_server_client.fetch(
        "/login", method="POST", body="username=", request_timeout=100000, raise_error=False
    )

    assert response.code == 404
