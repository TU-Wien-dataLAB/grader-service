# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import os
from re import S
from unittest.mock import patch, MagicMock

import pytest
from sqlalchemy.orm import Session, sessionmaker, scoped_session

from grader_service import handlers  # need import to register handlers
from grader_service.registry import HandlerPathRegistry
from grader_service.server import GraderServer
# import alembic
from alembic import config
from alembic.command import upgrade
from .db_util import insert_assignments, insert_lectures

__all__ = ["db_test_config", "sql_alchemy_engine", "app", "service_base_url", "default_user",
           "default_token", "default_roles", "default_user_login", "default_roles_dict", "sql_alchemy_sessionmaker"]

from ...auth.dummy import DummyAuthenticator
from ...main import GraderService, get_session_maker
from ...orm import User, Role, Lecture
from ...orm.takepart import Scope


@pytest.fixture(scope="function")
def default_user_login(default_user, sql_alchemy_engine):
    engine = sql_alchemy_engine
    session: Session = sessionmaker(engine)()
    user = session.get(User, default_user.name)

    with patch.object(handlers.base_handler.BaseHandler, "_grader_user", new=user, create=True):
        yield


@pytest.fixture(scope="function")
def default_roles_dict():
    return {"20wle2": {"members": ["ubuntu"], "role": "instructor"},
            "21wle1": {"members": ["ubuntu"], "role": "student"},
            "22wle1": {"members": ["ubuntu"], "role": "instructor"}}


@pytest.fixture(scope="function")
def default_roles(sql_alchemy_sessionmaker, default_roles_dict):
    service_mock = MagicMock()
    service_mock.session_maker = sql_alchemy_sessionmaker
    service_mock.load_roles = default_roles_dict
    GraderService.init_roles(self=service_mock)



@pytest.fixture(scope="function")
def db_test_config():
    cfg = config.Config(
        os.path.abspath(os.path.dirname(__file__) + "../../../alembic_test.ini")
    )
    cfg.set_main_option("script_location", os.path.abspath(os.path.dirname(__file__) + "../../../migrate"))
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
    yield session_maker


@pytest.fixture(scope="function")
def app(tmpdir, sql_alchemy_sessionmaker):
    service_dir = str(tmpdir.mkdir("grader_service"))
    handlers = HandlerPathRegistry.handler_list()

    application = GraderServer(
        grader_service_dir=service_dir,
        base_url="/",
        authenticator=DummyAuthenticator(),
        handlers=handlers,
        oauth_provider=None,
        session_maker=sql_alchemy_sessionmaker,
        cookie_secret="test",
        login_url="/login",
        logout_url="/logout"
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
    user = User(name="ubuntu")
    yield user


@pytest.fixture(scope="function")
def default_token():
    token = "token"
    yield token
