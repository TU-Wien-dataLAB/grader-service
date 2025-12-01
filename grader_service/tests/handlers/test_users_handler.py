import json
from http import HTTPStatus

import pytest
from sqlalchemy.orm import Session, sessionmaker
from tornado.httpclient import HTTPClientError

from grader_service import orm
from grader_service.server import GraderServer
from grader_service.tests.handlers.db_util import (
    check_git_repositories,
    create_all_git_repositories,
    insert_submission,
)


async def test_get_users_unauthorized(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
    default_user,
):
    url = service_base_url + "users/"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.FORBIDDEN


async def test_get_users_admin_unknown_parameter(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_admin_login,
    default_user,
):
    url = service_base_url + "users/?abc=123"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.BAD_REQUEST


async def test_get_users_admin(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_admin_login,
    default_user,
    default_admin,
):
    url = service_base_url + "users/"

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK
    users = json.loads(response.body.decode())
    assert isinstance(users, list)
    assert len(users) == 2
    assert users[0]["name"] == default_user.name
    assert users[1]["name"] == default_admin.name


async def test_get_user_unauthorized(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
    default_user,
):
    url = service_base_url + f"users/{default_user.name}/"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.FORBIDDEN


async def test_get_user_admin_unknown_parameter(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_admin_login,
    default_user,
):
    url = service_base_url + f"users/{default_user.name}/?abc=123"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.BAD_REQUEST


async def test_get_user_admin(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_admin_login,
    default_user,
    default_admin,
):
    url = service_base_url + f"users/{default_user.name}"

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK
    user = json.loads(response.body.decode())
    assert user["name"] == default_user.name


async def test_get_user_admin_wrong_user(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_admin_login,
    default_user,
):
    url = service_base_url + "users/windows"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND


async def test_put_user_unauthorized(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
    default_user,
):
    url = service_base_url + f"users/{default_user.name}"

    data = {"name": default_user.name, "display_name": "New Name"}
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="PUT",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(data),
        )
    e = exc_info.value
    assert e.code == HTTPStatus.FORBIDDEN


async def test_put_user_admin_unknown_parameter(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_admin_login,
    default_user,
):
    url = service_base_url + f"users/{default_user.name}/?abc=123"

    data = {"name": default_user.name, "display_name": "New Name"}
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="PUT",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(data),
        )
    e = exc_info.value
    assert e.code == HTTPStatus.BAD_REQUEST


async def test_put_user_admin(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_admin_login,
    default_user,
    default_admin,
):
    url = service_base_url + f"users/{default_user.name}"

    data = {"name": default_user.name, "display_name": "New Name"}
    response = await http_server_client.fetch(
        url,
        method="PUT",
        headers={"Authorization": f"Token {default_token}"},
        body=json.dumps(data),
    )
    assert response.code == HTTPStatus.OK

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK
    user = json.loads(response.body.decode())
    assert user["name"] == default_user.name
    assert user["display_name"] == "New Name"


async def test_put_user_admin_wrong_user(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_admin_login,
    default_user,
):
    url = service_base_url + "users/windows"

    data = {"name": default_user.name, "display_name": "New Name"}
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="PUT",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(data),
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND


async def test_delete_user_unauthorized(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
    default_user,
):
    url = service_base_url + f"users/{default_user.name}"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.FORBIDDEN


async def test_delete_user_admin_unknown_parameter(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_admin_login,
    default_user,
):
    url = service_base_url + f"users/{default_user.name}/?abc=123"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.BAD_REQUEST


async def test_delete_user_admin(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_admin_login,
    default_user,
    default_admin,
    sql_alchemy_engine,
):
    username = default_user.name
    url = service_base_url + f"users/{username}/"

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK

    session: Session = sessionmaker(sql_alchemy_engine)()
    old_user = session.query(orm.User).filter(orm.User.name == username).first()

    orm.APIToken.new(user=old_user)

    auth_code = orm.OAuthCode(
        code="abc",
        expires_at=int(orm.OAuthCode.now() + 300),
        scopes=[orm.takepart.Scope.student],
        redirect_uri="redirect_uri",
        session_id="1234",
        user_id=old_user.id,
    )
    session.add(auth_code)
    session.commit()

    l_id = 1  # admin has no role
    l_code = "21wle1"
    a_id = 1
    s_id = 1
    insert_submission(sql_alchemy_engine, a_id, default_user.name, default_user.id)
    create_all_git_repositories(app, default_user, l_id, l_code, a_id, s_id)

    old_submissions = (
        session.query(orm.Submission).filter(orm.Submission.user_id == old_user.id).all()
    )
    old_roles = session.query(orm.Role).filter(orm.Role.user_id == old_user.id).all()
    old_api_tokens = session.query(orm.APIToken).filter(orm.APIToken.user_id == old_user.id).all()
    old_auth_codes = session.query(orm.OAuthCode).filter(orm.OAuthCode.user_id == old_user.id).all()

    assert old_user.name == username
    assert len(old_submissions) == 1
    assert len(old_roles) == 3
    assert len(old_api_tokens) == 1
    assert len(old_auth_codes) == 1

    response = await http_server_client.fetch(
        url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND

    user = session.query(orm.User).filter(orm.User.name == username).first()
    submissions = session.query(orm.Submission).filter(orm.Submission.user_id == old_user.id).all()
    roles = session.query(orm.Role).filter(orm.Role.user_id == old_user.id).all()
    api_tokens = session.query(orm.APIToken).filter(orm.APIToken.user_id == old_user.id).all()
    auth_codes = session.query(orm.OAuthCode).filter(orm.OAuthCode.user_id == old_user.id).all()

    assert user is None
    assert len(submissions) == 0
    assert len(roles) == 0
    assert len(api_tokens) == 0
    assert len(auth_codes) == 0

    check_git_repositories(
        app, default_user, l_code, a_id, s_id, True, True, True, False, False, False, False
    )


async def test_delete_user_admin_wrong_user(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_admin_login,
    default_user,
):
    url = service_base_url + "users/windows/"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND
