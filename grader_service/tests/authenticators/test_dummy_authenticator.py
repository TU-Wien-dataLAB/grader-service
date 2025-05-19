from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.orm import sessionmaker, Session

from grader_service.api.models.assignment_settings import AssignmentSettings
from grader_service.auth.dummy import DummyAuthenticator
from grader_service.auth.login import LoginHandler
from grader_service.auth.token import JupyterHubTokenAuthenticator, TokenLoginHandler
from grader_service.handlers.base_handler import BaseHandler
from grader_service.registry import HandlerPathRegistry
from grader_service.server import GraderServer
import json

from grader_service.api.models.lecture import Lecture
from ..handlers.db_util import insert_submission
from tornado.httpclient import HTTPClientError
from pytest_tornasync.plugin import AsyncHTTPServerClient
# Imports are important otherwise they will not be found
from ..handlers.tornado_test_utils import *
from ..handlers.db_util import insert_assignments
from ...orm import User

@pytest.fixture
def dummy_authenticator():
    authenticator = DummyAuthenticator()
    authenticator.allow_all = True
    yield authenticator


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
    app.add_handlers(host_pattern='.*', host_handlers=dummy_authenticator.get_handlers('/'))
    app.authenticator = dummy_authenticator

    with patch.object(LoginHandler, 'redirect', new=MagicMock()):
        response = await http_server_client.fetch('/login', method="GET", follow_redirects=False)

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
    user_mock = AsyncMock(return_value=None)


    app.add_handlers(host_pattern='.*', host_handlers=dummy_authenticator.get_handlers('/'))
    app.authenticator = dummy_authenticator
    
    
    response = await http_server_client.fetch(
    '/login', method="POST", body=f'username={default_user.name}&password=password', 
    follow_redirects=False, raise_error=False)


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

    app.add_handlers(host_pattern='.*', host_handlers=dummy_authenticator.get_handlers('/'))
    app.authenticator = dummy_authenticator
    
    response = await http_server_client.fetch(
    '/login', method="POST", body='username',request_timeout=100000)


    assert response.code == 404