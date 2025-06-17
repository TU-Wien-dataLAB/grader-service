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
from tornado.httpclient import HTTPClientError
from .db_util import insert_submission, insert_take_part

# Imports are important otherwise they will not be found
from .tornado_test_utils import *


async def test_get_permission(
        app: GraderServer,
        service_base_url,
        http_server_client,
        default_user,
        default_token,
        default_roles,
        default_user_login,
        default_roles_dict
):
    url = service_base_url + f"permissions"

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == 200
    permissions = json.loads(response.body.decode())
    assert isinstance(permissions, list)
    assert len(permissions) == 3

    def get_scope(v):
        if v == 0: return "student"
        if v == 1: return "tutor"
        if v == 2: return "instructor"

    groups = {(g, default_roles_dict[g]["role"]) for g in default_roles_dict.keys()}
    for p in permissions:
        t = (p["lecture_code"], get_scope(p["scope"]))
        assert t in groups
        groups.remove(t)
    assert len(groups) == 0
