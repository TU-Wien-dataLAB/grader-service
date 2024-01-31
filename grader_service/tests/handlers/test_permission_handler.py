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
    jupyter_hub_mock_server,
    default_user,
    default_token,
):
    default_user["groups"] = ["20wle2:instructor", "21wle1:student", "22wle1:instructor"]

    http_server = jupyter_hub_mock_server(default_user, default_token)
    app.auth_cls.hub_api_url = http_server.url_for("")[0:-1]
    url = service_base_url + f"/permissions"

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
    
    groups = {tuple(g.split(":")) for g in default_user["groups"]}
    for p in permissions:
        t = (p["lecture_code"], get_scope(p["scope"]))
        assert t in groups
        groups.remove(t)
    assert len(groups) == 0


async def test_get_permission_new_groups(
    app: GraderServer,
    service_base_url,
    http_server_client,
    jupyter_hub_mock_server,
    default_user,
    default_token,
):
    default_user["groups"] = ["pytest:tutor"]

    http_server = jupyter_hub_mock_server(default_user, default_token)
    app.auth_cls.hub_api_url = http_server.url_for("")[0:-1]
    url = service_base_url + f"/permissions/"

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == 200
    permissions = json.loads(response.body.decode())
    assert isinstance(permissions, list)
    assert len(permissions) == 1
    def get_scope(v):
        if v == 0: return "student"
        if v == 1: return "tutor"
        if v == 2: return "instructor"
    
    groups = {tuple(g.split(":")) for g in default_user["groups"]}
    for p in permissions:
        t = (p["lecture_code"], get_scope(p["scope"]))
        assert t in groups
        groups.remove(t)
    assert len(groups) == 0

