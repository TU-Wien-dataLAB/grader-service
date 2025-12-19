# Copyright (c) 2024, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import os
from unittest.mock import MagicMock, patch

import pytest
from alembic import config
from alembic.command import upgrade
from sqlalchemy import Engine, event
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from grader_service import GraderService, handlers
from grader_service.auth.dummy import DummyAuthenticator
from grader_service.main import get_session_maker
from grader_service.orm import User
from grader_service.orm.base import set_sqlite_pragma
from grader_service.registry import HandlerPathRegistry
from grader_service.server import GraderServer
from grader_service.tests.handlers.db_util import (
    insert_assignments,
    insert_default_user,
    insert_lectures,
)


@pytest.fixture(scope="function")
def enable_foreign_keys_for_sqlite():
    """
    Make sure the event listener is attached to the engine, and foreign keys
    are enabled for SQLite connections during the test.
    Remove the listener after the test runs to avoid interference with other tests.
    """
    assert event.contains(Engine, "connect", set_sqlite_pragma)
    yield

    # Remove the event listener to avoid interference with other tests
    event.remove(Engine, "connect", set_sqlite_pragma)


@pytest.fixture(scope="function")
def default_user_login(default_user, sql_alchemy_engine):
    engine = sql_alchemy_engine
    session: Session = sessionmaker(engine)()
    user = session.get(User, default_user.id)
    user.is_admin = False

    with patch.object(handlers.base_handler.BaseHandler, "_grader_user", new=user, create=True):
        yield


@pytest.fixture(scope="function")
def default_admin_login(default_admin, sql_alchemy_engine):
    engine = sql_alchemy_engine
    session: Session = sessionmaker(engine)()
    user = session.get(User, default_admin.id)
    user.is_admin = True

    with patch.object(handlers.base_handler.BaseHandler, "_grader_user", new=user, create=True):
        yield


@pytest.fixture(scope="function")
def default_roles_dict():
    return {
        "20wle2": [{"members": ["ubuntu"], "role": "instructor"}],
        "21wle1": [{"members": ["ubuntu"], "role": "student"}],
        "22wle1": [{"members": ["ubuntu"], "role": "instructor"}],
        "23wle1": [{"members": ["debian"], "role": "instructor"}],
    }


@pytest.fixture(scope="function")
def default_roles(sql_alchemy_sessionmaker, default_roles_dict):
    service_mock = MagicMock()
    service_mock.session_maker = sql_alchemy_sessionmaker
    service_mock.load_roles = default_roles_dict
    GraderService.init_roles(self=service_mock)


@pytest.fixture(scope="session")
def db_test_config():
    cfg = config.Config(os.path.abspath(os.path.dirname(__file__) + "../../alembic_test.ini"))
    cfg.set_main_option(
        "script_location", os.path.abspath(os.path.dirname(__file__) + "../../migrate")
    )
    yield cfg


@pytest.fixture(scope="function")
def sql_alchemy_sessionmaker(db_test_config):
    session_maker: scoped_session = get_session_maker(url="sqlite:///:memory:")
    session = session_maker()
    engine = session.get_bind()
    with engine.begin() as connection:
        db_test_config.attributes["connection"] = connection
        # downgrade(cfg, "base")
        upgrade(db_test_config, "head")
    insert_lectures(engine)
    insert_assignments(engine)
    insert_default_user(engine)
    yield session_maker


@pytest.fixture(scope="function")
def app(tmpdir, sql_alchemy_sessionmaker, default_admin):
    service_dir = str(tmpdir.mkdir("grader_service"))
    handlers = HandlerPathRegistry.handler_list()

    authenticator = DummyAuthenticator()
    authenticator.admin_users = [default_admin.name]

    application = GraderServer(
        grader_service_dir=service_dir,
        base_url="/",
        authenticator=authenticator,
        handlers=handlers,
        oauth_provider=None,
        session_maker=sql_alchemy_sessionmaker,
        cookie_secret="test",
        login_url="/login",
        logout_url="/logout",
    )
    yield application


@pytest.fixture(scope="function")
def sql_alchemy_engine(sql_alchemy_sessionmaker):
    session = sql_alchemy_sessionmaker()
    engine = session.get_bind()
    yield engine
    session.close()


@pytest.fixture(scope="module")
def service_base_url():
    base_url = "/api/"
    yield base_url


@pytest.fixture(scope="function")
def default_user():
    user = User(id=1, name="ubuntu", display_name="ubuntu")
    yield user


@pytest.fixture(scope="function")
def default_admin():
    user = User(id=2, name="debian", display_name="debian")
    yield user


@pytest.fixture(scope="function")
def default_token():
    token = "token"
    yield token
