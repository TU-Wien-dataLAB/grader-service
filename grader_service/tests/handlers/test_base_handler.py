# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
import base64

import pytest
import json
from grader_service.handlers.base_handler import GraderBaseHandler, BaseHandler
from grader_service.orm.assignment import Assignment
from datetime import datetime
from grader_service.api.models.error_message import ErrorMessage
from grader_service.orm.lecture import Lecture
from sqlalchemy.orm import sessionmaker

from .db_util import *
from .tornado_test_utils import *
from unittest.mock import AsyncMock, MagicMock, Mock
import asyncio


def test_string_serialization():
    assert GraderBaseHandler._serialize("test") == "test"


def test_number_serialization():
    assert GraderBaseHandler._serialize(1) == 1
    assert GraderBaseHandler._serialize(2.5) == 2.5


def test_list_serialization():
    assert GraderBaseHandler._serialize([1, 2, 3]) == [1, 2, 3]


def test_list_serialization_empty():
    assert GraderBaseHandler._serialize([]) == []


def test_tuple_serialization():
    assert GraderBaseHandler._serialize((1, 2, 3)) == (1, 2, 3)


def test_dict_serialization():
    d = {"a": 1, "b": "test", 5: 6}
    s = GraderBaseHandler._serialize(d)
    assert d == s


def test_dict_serialization_empty():
    d = {}
    s = GraderBaseHandler._serialize(d)
    assert d == s


def test_datetime_serialization():
    d = datetime.now(tz=timezone.utc)
    s = GraderBaseHandler._serialize(d)
    assert type(s) == str
    assert str(d) == s


def test_assignment_serialization():
    d = {
        "id": 1,
        "name": "test",
        "status": "created",
        'points': 0,
        'settings': {'late_submission': None,
                     'deadline':datetime.now(tz=timezone.utc).isoformat(),
                     'max_submissions': 1,
                     'autograde_type': 'unassisted',
                     'assignment_type': "user",
                     'allowed_files': None}
    }
    a = Assignment(
        id=d["id"],
        name=d["name"],
        lectid=1,
        points=0,
        status=d["status"],
        settings=d["settings"]
    )

    assert GraderBaseHandler._serialize(a) == d


def test_nested_serialization():
    o = [{"b": None}, {"a": 2}, "test", {"z": []}]
    s = GraderBaseHandler._serialize(o)
    assert o == s


def test_api_model_serialization():
    err = ErrorMessage("")


@pytest.mark.parametrize(["token_str"],
                         [("Token test",), ("Bearer test",), (f"Basic {base64.b64encode(b'test:test').decode('utf-8')}",)])
def test_get_auth_token(token_str):
    handler = MagicMock()
    handler.request.headers.get = MagicMock(return_value=token_str)
    assert BaseHandler.get_auth_token(self=handler) == "test"
