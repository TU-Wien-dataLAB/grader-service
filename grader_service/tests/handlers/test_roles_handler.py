import json
from http import HTTPStatus

import pytest
from tornado.httpclient import HTTPClientError

from grader_service.orm.takepart import Scope
from grader_service.server import GraderServer


async def test_get_roles_unauthorized(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
    default_user,
):
    l_id = 2
    url = service_base_url + f"lectures/{l_id}/roles/"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.FORBIDDEN


async def test_get_roles_admin_unknown_parameter(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_admin_login,
    default_user,
):
    l_id = 2
    url = service_base_url + f"lectures/{l_id}/roles/?abc=123"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.BAD_REQUEST


async def test_get_roles_admin(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_admin_login,
    default_user,
):
    l_id = 2
    url = service_base_url + f"lectures/{l_id}/roles/"

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK
    roles = json.loads(response.body.decode())
    assert isinstance(roles, list)
    assert len(roles) == 1
    assert roles[0]["user_id"] == default_user.id


async def test_get_roles_admin_wrong_lecture(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_admin_login,
    default_user,
):
    l_id = 999
    url = service_base_url + f"lectures/{l_id}/roles/"

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK
    roles = json.loads(response.body.decode())
    assert isinstance(roles, list)
    assert len(roles) == 0


async def test_post_roles_unauthorized(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
    default_user,
):
    l_id = 2
    url = service_base_url + f"lectures/{l_id}/roles/"

    data = {
        "users": [
            {
                "username": default_user.name,
                "role": Scope.student,
            }  # change role from instructor to student
        ]
    }
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="POST",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(data),
        )
    e = exc_info.value
    assert e.code == HTTPStatus.FORBIDDEN


async def test_post_roles_admin_unknown_parameter(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_admin_login,
    default_user,
):
    l_id = 2
    url = service_base_url + f"lectures/{l_id}/roles/?abc=123"

    data = {
        "users": [
            {
                "username": default_user.name,
                "role": Scope.student,
            }  # change role from instructor to student
        ]
    }
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="POST",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(data),
        )
    e = exc_info.value
    assert e.code == HTTPStatus.BAD_REQUEST


async def test_post_roles_admin(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_admin_login,
    default_user,
    default_admin,
):
    l_id = 2
    url = service_base_url + f"lectures/{l_id}/roles/"

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    roles = json.loads(response.body.decode())
    assert len(roles) == 1
    assert roles[0]["user_id"] == default_user.id
    assert roles[0]["role"] == Scope.instructor

    data = {
        "users": [
            {
                "username": default_user.name,
                "role": Scope.student,
            },  # change role from instructor to student
            {"username": default_admin.name, "role": Scope.instructor},  # new role
        ]
    }
    response = await http_server_client.fetch(
        url,
        method="POST",
        headers={"Authorization": f"Token {default_token}"},
        body=json.dumps(data),
    )
    assert response.code == HTTPStatus.CREATED

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK
    roles = json.loads(response.body.decode())
    assert isinstance(roles, list)
    assert len(roles) == 2
    assert roles[0]["user_id"] == default_user.id
    assert roles[0]["role"] == Scope.student
    assert roles[1]["user_id"] == default_admin.id
    assert roles[1]["role"] == Scope.instructor


async def test_post_roles_admin_wrong_lecture(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_admin_login,
    default_user,
):
    l_id = 999
    url = service_base_url + f"lectures/{l_id}/roles/"

    data = {
        "users": [
            {
                "username": default_user.name,
                "role": Scope.student,
            }  # change role from instructor to student
        ]
    }
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="POST",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(data),
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND


async def test_delete_roles_unauthorized(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
    default_user,
):
    l_id = 2
    url = service_base_url + f"lectures/{l_id}/roles/?usernames={default_user.name}"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.FORBIDDEN


async def test_delete_roles_admin_unknown_parameter(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_admin_login,
    default_user,
):
    l_id = 2
    url = service_base_url + f"lectures/{l_id}/roles/?abc=123&usernames={default_user.name}"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.BAD_REQUEST


async def test_delete_roles_admin(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_admin_login,
    default_user,
    default_admin,
):
    l_id = 2
    url = service_base_url + f"lectures/{l_id}/roles/"

    data = {
        "users": [
            {
                "username": default_user.name,
                "role": Scope.student,
            },  # change role from instructor to student
            {"username": default_admin.name, "role": Scope.instructor},  # new role
        ]
    }
    response = await http_server_client.fetch(
        url,
        method="POST",
        headers={"Authorization": f"Token {default_token}"},
        body=json.dumps(data),
    )
    assert response.code == HTTPStatus.CREATED

    response = await http_server_client.fetch(
        f"{url}?usernames={default_user.name}",
        method="DELETE",
        headers={"Authorization": f"Token {default_token}"},
    )
    assert response.code == HTTPStatus.OK

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK
    roles = json.loads(response.body.decode())
    assert isinstance(roles, list)
    assert len(roles) == 1
    assert roles[0]["user_id"] == default_admin.id
    assert roles[0]["role"] == Scope.instructor


async def test_delete_roles_admin_multiple(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_admin_login,
    default_user,
    default_admin,
):
    l_id = 2
    url = service_base_url + f"lectures/{l_id}/roles/"

    data = {
        "users": [
            {
                "username": default_user.name,
                "role": Scope.student,
            },  # change role from instructor to student
            {"username": default_admin.name, "role": Scope.instructor},  # new role
        ]
    }
    response = await http_server_client.fetch(
        url,
        method="POST",
        headers={"Authorization": f"Token {default_token}"},
        body=json.dumps(data),
    )
    assert response.code == HTTPStatus.CREATED

    response = await http_server_client.fetch(
        f"{url}?usernames={default_user.name},{default_admin.name}",
        method="DELETE",
        headers={"Authorization": f"Token {default_token}"},
    )
    assert response.code == HTTPStatus.OK

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK
    roles = json.loads(response.body.decode())
    assert isinstance(roles, list)
    assert len(roles) == 0


async def test_delete_roles_admin_multiple_wrong_user(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_admin_login,
    default_user,
    default_admin,
):
    l_id = 2
    url = service_base_url + f"lectures/{l_id}/roles/"

    data = {
        "users": [
            {
                "username": default_user.name,
                "role": Scope.student,
            },  # change role from instructor to student
            {"username": default_admin.name, "role": Scope.instructor},  # new role
        ]
    }
    response = await http_server_client.fetch(
        url,
        method="POST",
        headers={"Authorization": f"Token {default_token}"},
        body=json.dumps(data),
    )
    assert response.code == HTTPStatus.CREATED

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            f"{url}?usernames={default_user.name},{default_admin.name},windows",
            method="DELETE",
            headers={"Authorization": f"Token {default_token}"},
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK
    roles = json.loads(response.body.decode())
    assert isinstance(roles, list)
    assert len(roles) == 2


async def test_delete_roles_admin_empty_usernames(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_admin_login,
    default_user,
    default_admin,
):
    l_id = 2
    url = service_base_url + f"lectures/{l_id}/roles/"

    data = {
        "users": [
            {
                "username": default_user.name,
                "role": Scope.student,
            },  # change role from instructor to student
            {"username": default_admin.name, "role": Scope.instructor},  # new role
        ]
    }
    response = await http_server_client.fetch(
        url,
        method="POST",
        headers={"Authorization": f"Token {default_token}"},
        body=json.dumps(data),
    )
    assert response.code == HTTPStatus.CREATED

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.BAD_REQUEST


async def test_delete_roles_admin_wrong_lecture(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_admin_login,
    default_user,
):
    l_id = 999
    url = service_base_url + f"lectures/{l_id}/roles/usernames={default_user.name}"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND
