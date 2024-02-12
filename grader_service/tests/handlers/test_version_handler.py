# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import pytest
from grader_service.server import GraderServer

## Imports are important otherwise they will not be found
from .tornado_test_utils import *


# @pytest.mark.asyncio
async def test_version_handler(
    app: GraderServer,
    service_base_url,
    http_server_client,
    jupyter_hub_mock_server,
    default_user,
    default_token
):
    http_server = jupyter_hub_mock_server(default_user, default_token)
    app.auth_cls.hub_api_url = http_server.url_for("")

    url = service_base_url + "/"
    response = await http_server_client.fetch(url, headers={"Authorization": f"Token {default_token}"})
    assert response.code == 200
    assert response.body.decode() == "1.0"


async def test_version_handler_with_specifier(
    app: GraderServer,
    service_base_url,
    http_server_client,
    jupyter_hub_mock_server,
    default_user,
    default_token
):
    http_server = jupyter_hub_mock_server(default_user, default_token)
    app.auth_cls.hub_api_url = http_server.url_for("")

    url = service_base_url + "/v1/"
    response = await http_server_client.fetch(url, headers={"Authorization": f"Token {default_token}"})
    assert response.code == 200
    assert response.body.decode() == "1.0"