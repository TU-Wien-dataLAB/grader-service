# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

from grader_service import __version__
from grader_service.server import GraderServer


# @pytest.mark.asyncio
async def test_version_handler(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    default_roles,
    default_user_login,
):
    url = "/"
    response = await http_server_client.fetch(
        url, headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == 200
    assert response.body.decode() == f"Version {__version__}"


async def test_version_handler_with_specifier(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    default_roles,
    default_user_login,
):
    url = "/v1/"
    response = await http_server_client.fetch(
        url, headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == 200
    assert response.body.decode() == "Version 1.0"
