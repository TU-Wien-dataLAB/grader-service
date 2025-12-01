# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import json

from grader_service.server import GraderServer


async def test_get_permission(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    default_roles,
    default_user_login,
    default_roles_dict,
):
    url = service_base_url + "permissions"

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == 200
    permissions = json.loads(response.body.decode())
    assert isinstance(permissions, list)

    def get_scope(v):
        if v == 0:
            return "student"
        if v == 1:
            return "tutor"
        if v == 2:
            return "instructor"

    # build set of (lecture_code, role) pairs from all dict entries
    groups = set()
    for lecture_code, roles_list in default_roles_dict.items():
        for role_entry in roles_list:
            if default_user.name in role_entry["members"]:
                groups.add((lecture_code, role_entry["role"]))

    for p in permissions:
        t = (p["lecture_code"], get_scope(p["scope"]))
        assert t in groups
        groups.remove(t)
    assert len(groups) == 0
