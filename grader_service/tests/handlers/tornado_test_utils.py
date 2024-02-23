# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import os
from re import S
import pytest
from grader_service import handlers  # need import to register handlers
from grader_service.registry import HandlerPathRegistry
from grader_service.server import GraderServer
from tornado_sqlalchemy import SQLAlchemy
# import alembic
from alembic import config
from alembic.command import upgrade
from .db_util import insert_assignments, insert_lectures

__all__ = ["db_test_config", "sql_alchemy_db", "app", "service_base_url", "jupyter_hub_mock_server", "default_user", "default_token"]

from ...auth.hub import JupyterHubGroupAuthenticator


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

    JupyterHubGroupAuthenticator.hub_api_url = ""
    application = GraderServer(
        grader_service_dir=service_dir,
        base_url="/services/grader",
        auth_cls=JupyterHubGroupAuthenticator,
        handlers=handlers,
        db=sql_alchemy_db,
        cookie_secret="test",
    )
    yield application


@pytest.fixture(scope="module")
def service_base_url():
    base_url = "/services/grader"
    yield base_url


@pytest.fixture(scope="function")
def jupyter_hub_mock_server(httpserver):
    def for_user(login_user: dict, token: str):
        httpserver.expect_request(f"/user").respond_with_json(
            login_user
        )
        return httpserver

    yield for_user

@pytest.fixture(scope="function")
def default_user():
    user = {
        "kind": "user",
        "name": "ubuntu",
        "admin": False,
        "groups": ["20wle2:instructor", "21wle1:student", "22wle1:instructor"],
    }
    yield user

@pytest.fixture(scope="function")
def default_token():
    token = "token"
    yield token
