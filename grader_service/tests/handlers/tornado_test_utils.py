# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import os
from functools import wraps
from re import S
from unittest.mock import patch, MagicMock

import pytest
from sqlalchemy.orm import Session, sessionmaker

import grader_service.handlers.base_handler
from grader_service import handlers  # need import to register handlers
from grader_service.registry import HandlerPathRegistry
from grader_service.server import GraderServer
from tornado_sqlalchemy import SQLAlchemy
# import alembic
from alembic import config
from alembic.command import upgrade
from .db_util import insert_assignments, insert_lectures

__all__ = ["db_test_config", "sql_alchemy_db", "app", "service_base_url", "default_user",
           "default_token", "no_auth", "default_roles", "default_user_login", "default_roles_dict"]

from ...auth.dummy import DummyAuthenticator
from ...main import GraderService
from ...orm import User, Role, Lecture
from ...orm.takepart import Scope


@pytest.fixture(scope="function")
def default_user_login(default_user, sql_alchemy_db):
    engine = sql_alchemy_db.engine
    session: Session = sessionmaker(engine)()
    user = session.query(User).get(default_user.name)

    with patch.object(handlers.base_handler.BaseHandler, "_grader_user", new=user, create=True):
        yield


@pytest.fixture(scope="function")
def default_roles_dict():
    return {"20wle2:instructor": ["ubuntu"],
            "21wle1:student": ["ubuntu"],
            "22wle1:instructor": ["ubuntu"]}


@pytest.fixture(scope="function")
def default_roles(sql_alchemy_db, default_roles_dict):
    service_mock = MagicMock()
    service_mock.db.engine = sql_alchemy_db.engine
    service_mock.load_roles = default_roles_dict
    GraderService.init_roles(self=service_mock)


@pytest.fixture(scope='function')
def no_auth():
    with patch.object(grader_service.handlers.base_handler, attribute="check_authorization", return_value=True):
        yield


@pytest.fixture(scope="function")
def db_test_config():
    cfg = config.Config(
        os.path.abspath(os.path.dirname(__file__) + "../../../alembic_test.ini")
    )
    cfg.set_main_option("script_location", os.path.abspath(os.path.dirname(__file__) + "../../../migrate"))
    yield cfg


@pytest.fixture(scope="function")
def sql_alchemy_db(db_test_config):
    db = SQLAlchemy(url="sqlite:///:memory:")
    engine = db.engine
    with engine.begin() as connection:
        db_test_config.attributes["connection"] = connection
        # downgrade(cfg, "base")
        upgrade(db_test_config, "head")
    engine = db.engine
    insert_lectures(engine)
    insert_assignments(engine)
    yield db


@pytest.fixture(scope="function")
def app(tmpdir, sql_alchemy_db):
    service_dir = str(tmpdir.mkdir("grader_service"))
    handlers = HandlerPathRegistry.handler_list()

    application = GraderServer(
        grader_service_dir=service_dir,
        base_url="/services/grader",
        authenticator=DummyAuthenticator(),
        handlers=handlers,
        oauth_provider=None,
        db=sql_alchemy_db,
        cookie_secret="test",
    )
    yield application


@pytest.fixture(scope="module")
def service_base_url():
    base_url = "/services/grader"
    yield base_url


@pytest.fixture(scope="function")
def default_user():
    user = User(name="ubuntu")
    yield user


@pytest.fixture(scope="function")
def default_token():
    token = "token"
    yield token
