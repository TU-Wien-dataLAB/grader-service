# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
import json
from http import HTTPStatus

import pytest
from sqlalchemy.orm import Session, sessionmaker
from tornado.httpclient import HTTPClientError

from grader_service.api.models.assignment import Assignment
from grader_service.api.models.assignment_settings import AssignmentSettings
from grader_service.server import GraderServer

from ... import orm
from .db_util import (
    check_assignment_and_status,
    check_git_repositories,
    create_all_git_repositories,
    insert_assignment,
    insert_assignments,
    insert_submission,
)


async def test_get_assignments(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
):
    url = service_base_url + "lectures/1/assignments/"

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK
    assignments = json.loads(response.body.decode())
    assert isinstance(assignments, list)
    assert len(assignments) == 1
    [Assignment.from_dict(a) for a in assignments]  # assert no errors


async def test_get_assignments_admin(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_admin_login,
):
    url = service_base_url + "lectures/1/assignments/"

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK
    assignments = json.loads(response.body.decode())
    assert isinstance(assignments, list)
    assert len(assignments) == 2
    [Assignment.from_dict(a) for a in assignments]  # assert no errors


async def test_get_assignments_instructor(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 3  # default user is instructor
    url = service_base_url + f"lectures/{l_id}/assignments/"

    engine = sql_alchemy_engine
    num_inserted = insert_assignments(engine, l_id)

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK
    assignments = json.loads(response.body.decode())
    assert isinstance(assignments, list)
    assert len(assignments) == num_inserted
    [Assignment.from_dict(a) for a in assignments]  # assert no errors


async def test_get_assignments_lecture_deleted(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
):
    l_id = 3  # default user is instructor

    # delete lecture
    url = service_base_url + f"lectures/{l_id}/"
    delete_response = await http_server_client.fetch(
        url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
    )
    assert delete_response.code == HTTPStatus.OK

    url = service_base_url + f"lectures/{l_id}/assignments/"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND


async def test_post_assignment(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
):
    url = service_base_url + "lectures/3/assignments/"

    get_response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert get_response.code == HTTPStatus.OK
    assignments = json.loads(get_response.body.decode())
    assert isinstance(assignments, list)
    orig_len = len(assignments)

    pre_assignment = Assignment(
        id=-1,
        name="pytest",
        status="created",
        settings=AssignmentSettings(autograde_type="unassisted"),
    )
    post_response = await http_server_client.fetch(
        url,
        method="POST",
        headers={"Authorization": f"Token {default_token}"},
        body=json.dumps(pre_assignment.to_dict()),
    )
    assert post_response.code == HTTPStatus.CREATED
    post_assignment = Assignment.from_dict(json.loads(post_response.body.decode()))
    assert post_assignment.id != pre_assignment.id
    assert post_assignment.name == pre_assignment.name
    assert post_assignment.status == pre_assignment.status
    assert post_assignment.settings.deadline is None
    assert post_assignment.points == 0.0

    get_response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert get_response.code == HTTPStatus.OK
    assignments = json.loads(get_response.body.decode())
    assert len(assignments) == orig_len + 1


async def test_post_assignment_name_already_used(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
):
    url = service_base_url + "lectures/3/assignments/"

    post_assignment = Assignment(
        id=-1,
        name="pytest",
        status="created",
        settings=AssignmentSettings(autograde_type="unassisted"),
    )
    post_response = await http_server_client.fetch(
        url,
        method="POST",
        headers={"Authorization": f"Token {default_token}"},
        body=json.dumps(post_assignment.to_dict()),
    )
    assert post_response.code == HTTPStatus.CREATED

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="POST",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(post_assignment.to_dict()),
        )
    e = exc_info.value
    assert e.code == HTTPStatus.CONFLICT


async def test_put_assignment_name_already_used(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
):
    post_url = service_base_url + "lectures/3/assignments/"

    # Add assignments first
    post_assignment = Assignment(
        id=-1,
        name="pytest",
        status="created",
        settings=AssignmentSettings(autograde_type="unassisted"),
    )
    post_assignment_2 = Assignment(
        id=-2,
        name="pytest2",
        status="created",
        points=0,
        settings=AssignmentSettings(autograde_type="unassisted"),
    )
    post_response = await http_server_client.fetch(
        post_url,
        method="POST",
        headers={"Authorization": f"Token {default_token}"},
        body=json.dumps(post_assignment.to_dict()),
    )
    post_response_2 = await http_server_client.fetch(
        post_url,
        method="POST",
        headers={"Authorization": f"Token {default_token}"},
        body=json.dumps(post_assignment_2.to_dict()),
    )
    assert post_response.code == HTTPStatus.CREATED
    assert post_response_2.code == HTTPStatus.CREATED

    # Convert bytes body to json
    json_body = json.loads(post_response.body.decode("utf8"))
    put_url = post_url + str(json_body["id"])
    # Update assignment 1 with name of assignment 2
    post_assignment.name = post_assignment_2.name
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            put_url,
            method="PUT",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(post_assignment.to_dict()),
        )
    e = exc_info.value
    assert e.code == HTTPStatus.CONFLICT


async def test_post_assignment_lecture_deleted(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
):
    l_id = 3  # default user is instructor

    # delete lecture
    url = service_base_url + f"lectures/{l_id}/"
    delete_response = await http_server_client.fetch(
        url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
    )
    assert delete_response.code == HTTPStatus.OK

    url = service_base_url + "lectures/3/assignments/"
    post_assignment = Assignment(
        id=-1,
        name="pytest",
        status="created",
        settings=AssignmentSettings(autograde_type="unassisted"),
    )
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="POST",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(post_assignment.to_dict()),
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND


async def test_post_assignment_decode_error(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
):
    url = service_base_url + "lectures/3/assignments/"

    # no assignment status given
    pre_assignment = Assignment(id=-1, name="pytest", settings=AssignmentSettings())
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="POST",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(pre_assignment.to_dict()),
        )
    e = exc_info.value
    assert e.code == HTTPStatus.BAD_REQUEST

    # no autograde type given
    pre_assignment = Assignment(
        id=-1, name="pytest", status="created", settings=AssignmentSettings(autograde_type=None)
    )
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="POST",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(pre_assignment.to_dict()),
        )
    e = exc_info.value
    assert e.code == HTTPStatus.BAD_REQUEST


async def test_post_assignment_missing_vars(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
):
    l_id = 3  # default user is instructor
    url = service_base_url + f"lectures/{l_id}/assignments/"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="POST",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps({"some": "value"}),
        )
    e = exc_info.value
    assert e.code == HTTPStatus.BAD_REQUEST


async def test_post_no_status_error(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
):
    url = service_base_url + "lectures/3/assignments/"

    pre_assignment = Assignment(id=-1, name="pytest", settings=AssignmentSettings())
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="POST",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(pre_assignment.to_dict()),
        )
    e = exc_info.value
    assert e.code == HTTPStatus.BAD_REQUEST


async def test_put_assignment(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
):
    url = service_base_url + "lectures/3/assignments/"

    pre_assignment = Assignment(
        id=-1,
        name="pytest",
        status="created",
        settings=AssignmentSettings(autograde_type="unassisted"),
    )
    post_response = await http_server_client.fetch(
        url,
        method="POST",
        headers={"Authorization": f"Token {default_token}"},
        body=json.dumps(pre_assignment.to_dict()),
    )
    assert post_response.code == HTTPStatus.CREATED
    post_assignment = Assignment.from_dict(json.loads(post_response.body.decode()))

    post_assignment.name = "new name"
    post_assignment.status = "released"

    url = url + str(post_assignment.id)

    put_response = await http_server_client.fetch(
        url,
        method="PUT",
        headers={"Authorization": f"Token {default_token}"},
        body=json.dumps(post_assignment.to_dict()),
    )
    assert put_response.code == HTTPStatus.OK
    put_assignment = Assignment.from_dict(json.loads(put_response.body.decode()))
    assert put_assignment.id == post_assignment.id
    assert put_assignment.name == "new name"
    assert put_assignment.status == "released"


async def test_put_assignment_wrong_lecture_id(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
):
    # default user becomes instructor in lecture with id 3
    url = service_base_url + "lectures/3/assignments/"

    pre_assignment = Assignment(
        id=-1,
        name="pytest",
        status="created",
        settings=AssignmentSettings(autograde_type="unassisted"),
    )
    post_response = await http_server_client.fetch(
        url,
        method="POST",
        headers={"Authorization": f"Token {default_token}"},
        body=json.dumps(pre_assignment.to_dict()),
    )
    assert post_response.code == HTTPStatus.CREATED
    post_assignment = Assignment.from_dict(json.loads(post_response.body.decode()))

    # now with lecture id 2 because user would be instructor there too
    url = service_base_url + "lectures/2/assignments/" + str(post_assignment.id)

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="PUT",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(post_assignment.to_dict()),
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND


async def test_put_assignment_wrong_assignment_id(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
):
    url = service_base_url + "lectures/3/assignments/"

    pre_assignment = Assignment(
        id=-1, name="pytest", status="created", settings=AssignmentSettings()
    )
    post_response = await http_server_client.fetch(
        url,
        method="POST",
        headers={"Authorization": f"Token {default_token}"},
        body=json.dumps(pre_assignment.to_dict()),
    )
    assert post_response.code == HTTPStatus.CREATED
    post_assignment = Assignment.from_dict(json.loads(post_response.body.decode()))

    url = url + "99"
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="PUT",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(post_assignment.to_dict()),
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND


async def test_put_assignment_deleted_assignment(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
):
    url = service_base_url + "lectures/3/assignments/"

    pre_assignment = Assignment(
        id=-1,
        name="pytest",
        status="created",
        settings=AssignmentSettings(autograde_type="unassisted"),
    )
    post_response = await http_server_client.fetch(
        url,
        method="POST",
        headers={"Authorization": f"Token {default_token}"},
        body=json.dumps(pre_assignment.to_dict()),
    )
    assert post_response.code == HTTPStatus.CREATED
    post_assignment = Assignment.from_dict(json.loads(post_response.body.decode()))

    url = url + str(post_assignment.id)

    delete_response = await http_server_client.fetch(
        url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
    )
    assert delete_response.code == HTTPStatus.OK

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="PUT",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(post_assignment.to_dict()),
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND
    assert e.message == f"Assignment with id {post_assignment.id} was not found"


async def test_put_assignment_no_point_changes(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
):
    url = service_base_url + "lectures/3/assignments/"

    pre_assignment = Assignment(
        id=-1,
        name="pytest",
        status="created",
        settings=AssignmentSettings(autograde_type="unassisted"),
    )
    post_response = await http_server_client.fetch(
        url,
        method="POST",
        headers={"Authorization": f"Token {default_token}"},
        body=json.dumps(pre_assignment.to_dict()),
    )
    assert post_response.code == HTTPStatus.CREATED
    post_assignment = Assignment.from_dict(json.loads(post_response.body.decode()))

    post_assignment.name = "new name"
    post_assignment.status = "released"
    post_assignment.points = 10.0  # this has no effect

    url = url + str(post_assignment.id)

    put_response = await http_server_client.fetch(
        url,
        method="PUT",
        headers={"Authorization": f"Token {default_token}"},
        body=json.dumps(post_assignment.to_dict()),
    )
    assert put_response.code == HTTPStatus.OK
    put_assignment = Assignment.from_dict(json.loads(put_response.body.decode()))
    assert put_assignment.id == post_assignment.id
    assert put_assignment.name == "new name"
    assert put_assignment.status == "released"
    assert put_assignment.points != 10.0


async def test_get_assignment(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
):
    url = service_base_url + "lectures/3/assignments/"

    pre_assignment = Assignment(
        id=-1,
        name="pytest",
        status="created",
        settings=AssignmentSettings(autograde_type="unassisted"),
    )
    post_response = await http_server_client.fetch(
        url,
        method="POST",
        headers={"Authorization": f"Token {default_token}"},
        body=json.dumps(pre_assignment.to_dict()),
    )
    assert post_response.code == HTTPStatus.CREATED
    post_assignment = Assignment.from_dict(json.loads(post_response.body.decode()))

    url = url + str(post_assignment.id)

    get_response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert get_response.code == HTTPStatus.OK
    get_assignment = Assignment.from_dict(json.loads(get_response.body.decode()))
    assert get_assignment.id == post_assignment.id
    assert get_assignment.name == post_assignment.name
    assert get_assignment.status == post_assignment.status
    assert get_assignment.points == post_assignment.points
    assert get_assignment.settings.deadline == post_assignment.settings.deadline


async def test_get_assignment_created_student(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
    sql_alchemy_engine,
):
    l_id = 1  # default user is student
    a_id = 2  # assignment is created
    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}"

    check_assignment_and_status(sql_alchemy_engine, l_id=l_id, a_id=a_id, status="created")

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    assert exc_info.value.code == HTTPStatus.NOT_FOUND


async def test_get_assignment_created_admin(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_admin_login,
    sql_alchemy_engine,
):
    l_id = 1  # default user is admin
    a_id = 2  # assignment is created
    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}"

    check_assignment_and_status(sql_alchemy_engine, l_id=l_id, a_id=a_id, status="created")

    get_response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert get_response.code == HTTPStatus.OK
    Assignment.from_dict(json.loads(get_response.body.decode()))


async def test_get_assignment_unauthorized(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
    sql_alchemy_engine,
):
    l_id = 4  # default user has no role
    a_id = 3  # assignment is released
    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}"

    insert_assignments(sql_alchemy_engine, l_id)
    check_assignment_and_status(sql_alchemy_engine, l_id=l_id, a_id=a_id, status="released")

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    assert exc_info.value.code == HTTPStatus.FORBIDDEN


async def test_get_assignment_wrong_lecture_id(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
):
    l_id = 3
    url = service_base_url + f"lectures/{l_id}/assignments/"

    pre_assignment = Assignment(
        id=-1,
        name="pytest",
        status="created",
        settings=AssignmentSettings(autograde_type="unassisted"),
    )
    post_response = await http_server_client.fetch(
        url,
        method="POST",
        headers={"Authorization": f"Token {default_token}"},
        body=json.dumps(pre_assignment.to_dict()),
    )
    assert post_response.code == HTTPStatus.CREATED
    post_assignment = Assignment.from_dict(json.loads(post_response.body.decode()))

    l_id = 1
    url = service_base_url + f"lectures/{l_id}/assignments/{post_assignment.id}"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    assert exc_info.value.code == HTTPStatus.NOT_FOUND


async def test_get_assignment_wrong_assignment_id(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
):
    l_id = 3
    url = service_base_url + f"lectures/{l_id}/assignments/"

    pre_assignment = Assignment(
        id=-1,
        name="pytest",
        status="created",
        settings=AssignmentSettings(autograde_type="unassisted"),
    )
    post_response = await http_server_client.fetch(
        url,
        method="POST",
        headers={"Authorization": f"Token {default_token}"},
        body=json.dumps(pre_assignment.to_dict()),
    )
    assert post_response.code == HTTPStatus.CREATED

    url = service_base_url + f"lectures/{l_id}/assignments/99"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    assert exc_info.value.code == HTTPStatus.NOT_FOUND


async def test_get_assignment_unknown_parameter(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 3
    url = service_base_url + f"lectures/{l_id}/assignments/4/?instructor-version=true"

    engine = sql_alchemy_engine
    insert_assignments(engine, 3)

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    assert exc_info.value.code == HTTPStatus.BAD_REQUEST


async def test_delete_assignment(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
    sql_alchemy_engine,
):
    l_id = 3

    url = service_base_url + f"lectures/{l_id}/assignments/"

    pre_assignment = Assignment(
        id=-1,
        name="pytest",
        status="created",
        settings=AssignmentSettings(autograde_type="unassisted"),
    )
    post_response = await http_server_client.fetch(
        url,
        method="POST",
        headers={"Authorization": f"Token {default_token}"},
        body=json.dumps(pre_assignment.to_dict()),
    )
    assert post_response.code == HTTPStatus.CREATED
    post_assignment = Assignment.from_dict(json.loads(post_response.body.decode()))

    url = url + str(post_assignment.id)

    delete_response = await http_server_client.fetch(
        url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
    )
    assert delete_response.code == HTTPStatus.OK
    check_assignment_and_status(
        sql_alchemy_engine, l_id=l_id, a_id=post_assignment.id, status="created"
    )

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )

    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND
    assert e.message == f"Assignment with id {post_assignment.id} was not found"


async def test_delete_assignment_deleted_assignment(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
    sql_alchemy_engine,
):
    l_id = 3

    url = service_base_url + f"lectures/{l_id}/assignments/"

    pre_assignment = Assignment(
        id=-1,
        name="pytest",
        status="created",
        settings=AssignmentSettings(autograde_type="unassisted"),
    )
    post_response = await http_server_client.fetch(
        url,
        method="POST",
        headers={"Authorization": f"Token {default_token}"},
        body=json.dumps(pre_assignment.to_dict()),
    )
    assert post_response.code == HTTPStatus.CREATED
    post_assignment = Assignment.from_dict(json.loads(post_response.body.decode()))

    url = url + str(post_assignment.id)

    delete_response = await http_server_client.fetch(
        url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
    )
    assert delete_response.code == HTTPStatus.OK
    check_assignment_and_status(
        sql_alchemy_engine, l_id=l_id, a_id=post_assignment.id, status="created"
    )

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
        )

    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND
    assert e.message == f"Assignment with id {post_assignment.id} was not found"


async def test_delete_assignment_not_found(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
):
    url = service_base_url + "lectures/3/assignments/-5"
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND


async def test_delete_assignment_not_created(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
):
    url = service_base_url + "lectures/3/assignments/999"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND


async def test_delete_assignment_same_name_twice(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
    sql_alchemy_engine,
):
    l_id = 3

    url = service_base_url + f"lectures/{l_id}/assignments/"

    pre_assignment = Assignment(
        id=-1,
        name="pytest",
        status="created",
        settings=AssignmentSettings(autograde_type="unassisted"),
    )
    post_response = await http_server_client.fetch(
        url,
        method="POST",
        headers={"Authorization": f"Token {default_token}"},
        body=json.dumps(pre_assignment.to_dict()),
    )
    assert post_response.code == HTTPStatus.CREATED
    first_post_assignment = Assignment.from_dict(json.loads(post_response.body.decode()))

    url = url + str(first_post_assignment.id)

    delete_response = await http_server_client.fetch(
        url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
    )
    assert delete_response.code == HTTPStatus.OK
    check_assignment_and_status(
        sql_alchemy_engine, l_id=l_id, a_id=first_post_assignment.id, status="created"
    )

    url = service_base_url + "lectures/3/assignments/"

    post_response = await http_server_client.fetch(
        url,
        method="POST",
        headers={"Authorization": f"Token {default_token}"},
        body=json.dumps(pre_assignment.to_dict()),
    )
    assert post_response.code == HTTPStatus.CREATED
    second_post_assignment = Assignment.from_dict(json.loads(post_response.body.decode()))

    url = url + str(second_post_assignment.id)

    delete_response = await http_server_client.fetch(
        url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
    )
    assert delete_response.code == HTTPStatus.OK
    check_assignment_and_status(
        sql_alchemy_engine,
        l_id=l_id,
        a_id=first_post_assignment.id,
        status="created",
        should_exist=False,
    )
    check_assignment_and_status(
        sql_alchemy_engine, l_id=l_id, a_id=second_post_assignment.id, status="created"
    )


async def test_delete_released_assignment(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
):
    url = service_base_url + "lectures/3/assignments/"

    pre_assignment = Assignment(
        id=-1,
        name="pytest",
        status="released",
        settings=AssignmentSettings(autograde_type="unassisted"),
    )
    post_response = await http_server_client.fetch(
        url,
        method="POST",
        headers={"Authorization": f"Token {default_token}"},
        body=json.dumps(pre_assignment.to_dict()),
    )
    assert post_response.code == HTTPStatus.CREATED
    post_assignment = Assignment.from_dict(json.loads(post_response.body.decode()))

    url = url + str(post_assignment.id)

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.CONFLICT


async def test_delete_complete_assignment(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
):
    url = service_base_url + "lectures/3/assignments/"

    pre_assignment = Assignment(
        id=-1,
        name="pytest",
        status="complete",
        settings=AssignmentSettings(autograde_type="unassisted"),
    )
    post_response = await http_server_client.fetch(
        url,
        method="POST",
        headers={"Authorization": f"Token {default_token}"},
        body=json.dumps(pre_assignment.to_dict()),
    )
    assert post_response.code == HTTPStatus.CREATED
    post_assignment = Assignment.from_dict(json.loads(post_response.body.decode()))

    url = url + str(post_assignment.id)

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.CONFLICT


async def test_delete_assignment_with_submissions(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_user,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 3  # user has to be instructor
    a_id = 3
    engine = sql_alchemy_engine

    insert_assignments(engine, l_id)
    insert_submission(engine, a_id, default_user.name, default_user.id)

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.CONFLICT


async def test_delete_assignment_hard(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_admin_login,
    sql_alchemy_engine,
):
    l_id = 3
    a_id = 3

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}"

    insert_assignment(sql_alchemy_engine, l_id)

    delete_response = await http_server_client.fetch(
        url + "?hard_delete=true",
        method="DELETE",
        headers={"Authorization": f"Token {default_token}"},
    )
    assert delete_response.code == HTTPStatus.OK
    check_assignment_and_status(
        sql_alchemy_engine, l_id=l_id, a_id=a_id, status="created", should_exist=False
    )

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )

    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND
    assert e.message == f"Assignment with id {a_id} was not found"

    session: Session = sessionmaker(sql_alchemy_engine)()
    assignments = session.query(orm.Assignment).filter(orm.Assignment.lectid == l_id).all()
    assert len(assignments) == 0


async def test_delete_assignment_hard_unauthorized(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
    sql_alchemy_engine,
):
    l_id = 3
    a_id = 3

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}"

    insert_assignment(sql_alchemy_engine, l_id)

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url + "?hard_delete=true",
            method="DELETE",
            headers={"Authorization": f"Token {default_token}"},
        )
    e = exc_info.value
    assert e.code == HTTPStatus.FORBIDDEN


async def test_delete_assignment_hard_with_submissions(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_admin_login,
    sql_alchemy_engine,
    default_user,
):
    l_id = 4
    l_code = "23wle1"
    a_id = 3
    s_id = 1

    # create assignment
    url = service_base_url + f"lectures/{l_id}/assignments"
    pre_assignment = Assignment(
        id=-1, name="pytest", status="released", settings=AssignmentSettings()
    )
    post_response = await http_server_client.fetch(
        url,
        method="POST",
        headers={"Authorization": f"Token {default_token}"},
        body=json.dumps(pre_assignment.to_dict()),
    )
    assert post_response.code == HTTPStatus.CREATED

    insert_submission(sql_alchemy_engine, a_id, default_user.name, default_user.id)
    create_all_git_repositories(app, default_user, l_id, l_code, a_id, s_id)

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}"
    delete_response = await http_server_client.fetch(
        url + "?hard_delete=true",
        method="DELETE",
        headers={"Authorization": f"Token {default_token}"},
    )
    assert delete_response.code == HTTPStatus.OK
    check_assignment_and_status(
        sql_alchemy_engine, l_id=l_id, a_id=a_id, status="released", should_exist=False
    )

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )

    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND
    assert e.message == f"Assignment with id {a_id} was not found"

    session: Session = sessionmaker(sql_alchemy_engine)()
    assignments = session.query(orm.Assignment).filter(orm.Assignment.lectid == l_id).all()
    assert len(assignments) == 0

    submissions = session.query(orm.Submission).filter(orm.Submission.assignid == a_id).all()
    assert len(submissions) == 0

    check_git_repositories(
        app, default_user, l_code, a_id, False, False, False, False, False, False, False, False
    )


async def test_assignment_properties_lecture_assignment_missmatch(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 3
    a_id = 1
    engine = sql_alchemy_engine
    insert_assignments(engine, l_id)

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/properties"
    prop = {"notebooks": {}}

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="PUT",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(prop),
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND


async def test_assignment_properties_wrong_assignment_id(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 3
    a_id = 99
    engine = sql_alchemy_engine
    insert_assignments(engine, l_id)

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/properties"
    prop = {"notebooks": {}}

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="PUT",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(prop),
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND


async def test_assignment_properties_not_found(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 3
    a_id = 3
    engine = sql_alchemy_engine
    insert_assignments(engine, l_id)

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}/properties"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND


async def test_assignment_properties_properties_wrong_for_autograde(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    url = service_base_url + "lectures/3/assignments/"

    pre_assignment = Assignment(
        id=-1,
        name="pytest",
        status="created",
        settings=AssignmentSettings(autograde_type="full_auto"),
    )
    post_response = await http_server_client.fetch(
        url,
        method="POST",
        headers={"Authorization": f"Token {default_token}"},
        body=json.dumps(pre_assignment.to_dict()),
    )
    assert post_response.code == HTTPStatus.CREATED
    post_assignment = Assignment.from_dict(json.loads(post_response.body.decode()))
    assert post_assignment.settings.autograde_type == "full_auto"
    url = service_base_url + f"lectures/3/assignments/{post_assignment.id}/properties"
    prop = {
        "_type": "GradeBookModel",
        "notebooks": {
            "a5": {
                "_type": "Notebook",
                "comments_dict": {},
                "flagged": False,
                "grade_cells_dict": {
                    "cell-81540a070d18c412": {
                        "_type": "GradeCell",
                        "cell_type": "code",
                        "comment_id": None,
                        "grade_id": None,
                        "id": None,
                        "max_score": 1.0,
                        "name": "cell-81540a070d18c412",
                        "notebook_id": None,
                    },
                    "cell-9ea0264ada6c25bd": {
                        "_type": "GradeCell",
                        "cell_type": "markdown",
                        "comment_id": None,
                        "grade_id": None,
                        "id": None,
                        "max_score": 2.0,
                        "name": "cell-9ea0264ada6c25bd",
                        "notebook_id": None,
                    },
                    "cell-da8c82e850a1922b": {
                        "_type": "GradeCell",
                        "cell_type": "code",
                        "comment_id": None,
                        "grade_id": None,
                        "id": None,
                        "max_score": 1.0,
                        "name": "cell-da8c82e850a1922b",
                        "notebook_id": None,
                    },
                },
                "grades_dict": {},
                "id": "a5",
                "kernelspec": '{"display_name": "Python 3", "language": "python", "name": "python3"}',
                "name": "a5",
                "solution_cells_dict": {
                    "cell-28df1799f8f8b769": {
                        "_type": "SolutionCell",
                        "comment_id": None,
                        "grade_id": None,
                        "id": None,
                        "name": "cell-28df1799f8f8b769",
                        "notebook_id": None,
                    },
                    "cell-9ea0264ada6c25bd": {
                        "_type": "SolutionCell",
                        "comment_id": None,
                        "grade_id": None,
                        "id": None,
                        "name": "cell-9ea0264ada6c25bd",
                        "notebook_id": None,
                    },
                },
                "source_cells_dict": {
                    "cell-1b9d18df2b17e57f": {
                        "_type": "SourceCell",
                        "cell_type": "markdown",
                        "checksum": "92c710dde448a453c67a457a1a516266",
                        "id": None,
                        "locked": None,
                        "name": "cell-1b9d18df2b17e57f",
                        "notebook_id": None,
                        "source": '## Aufgabe 3\nDoes Java use "fake"-threads? Explain why or why not?',
                    },
                    "cell-26053a7da067ded3": {
                        "_type": "SourceCell",
                        "cell_type": "markdown",
                        "checksum": "341dd0694041ff4b5666c5ae94083cb4",
                        "id": None,
                        "locked": True,
                        "name": "cell-26053a7da067ded3",
                        "notebook_id": None,
                        "source": "### Aufgabe 1",
                    },
                    "cell-28df1799f8f8b769": {
                        "_type": "SourceCell",
                        "cell_type": "code",
                        "checksum": "bd34afadfba8f9e585d1245ca8d75beb",
                        "id": None,
                        "locked": False,
                        "name": "cell-28df1799f8f8b769",
                        "notebook_id": None,
                        "source": "def reverse(s):\n    # YOUR CODE HERE\n    raise NotImplementedError()",
                    },
                    "cell-58d7f9f371feee54": {
                        "_type": "SourceCell",
                        "cell_type": "markdown",
                        "checksum": "378450bc4a5678dafbcd41aa17baa337",
                        "id": None,
                        "locked": True,
                        "name": "cell-58d7f9f371feee54",
                        "notebook_id": None,
                        "source": '## Aufgabe 2\nWhat are "fake"-threads?',
                    },
                    "cell-81540a070d18c412": {
                        "_type": "SourceCell",
                        "cell_type": "code",
                        "checksum": "efff0d4fdfcbd070c4a9afa0afc914dc",
                        "id": None,
                        "locked": True,
                        "name": "cell-81540a070d18c412",
                        "notebook_id": None,
                        "source": "assert (reverse('lol') == 'lol')",
                    },
                    "cell-9ea0264ada6c25bd": {
                        "_type": "SourceCell",
                        "cell_type": "markdown",
                        "checksum": "cbcb81d7877ddde960682872f59d9578",
                        "id": None,
                        "locked": False,
                        "name": "cell-9ea0264ada6c25bd",
                        "notebook_id": None,
                        "source": "YOUR ANSWER HERE",
                    },
                    "cell-c06c761f0b7b0f59": {
                        "_type": "SourceCell",
                        "cell_type": "code",
                        "checksum": "4ce43bbad8e68a85ba3a7594ea9a41be",
                        "id": None,
                        "locked": True,
                        "name": "cell-c06c761f0b7b0f59",
                        "notebook_id": None,
                        "source": "reverse('Test')",
                    },
                    "cell-da8c82e850a1922b": {
                        "_type": "SourceCell",
                        "cell_type": "code",
                        "checksum": "5e838f105bec52e51e488e029e4727fd",
                        "id": None,
                        "locked": True,
                        "name": "cell-da8c82e850a1922b",
                        "notebook_id": None,
                        "source": "assert (reverse('Test') == 'tseT')",
                    },
                },
                "task_cells_dict": {
                    "cell-58d7f9f371feee54": {
                        "_type": "TaskCell",
                        "cell_type": "code",
                        "comment_id": None,
                        "grade_id": None,
                        "id": None,
                        "max_score": 2.0,
                        "name": "cell-58d7f9f371feee54",
                        "notebook_id": None,
                    }
                },
            }
        },
        "schema_version": "1",
    }
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="PUT",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(prop),
        )
    e = exc_info.value
    assert e.code == HTTPStatus.CONFLICT


async def test_assignment_properties_properties_manual_graded_with_auto_grading(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    url = service_base_url + "lectures/3/assignments/"

    pre_assignment = Assignment(
        id=-1,
        name="pytest",
        status="created",
        settings=AssignmentSettings(autograde_type="full_auto"),
    )
    post_response = await http_server_client.fetch(
        url,
        method="POST",
        headers={"Authorization": f"Token {default_token}"},
        body=json.dumps(pre_assignment.to_dict()),
    )
    assert post_response.code == HTTPStatus.CREATED
    post_assignment = Assignment.from_dict(json.loads(post_response.body.decode()))
    assert post_assignment.settings.autograde_type == "full_auto"
    url = service_base_url + f"lectures/3/assignments/{post_assignment.id}/properties"
    prop = {
        "_type": "GradeBookModel",
        "notebooks": {
            "a5": {
                "_type": "Notebook",
                "comments_dict": {},
                "flagged": False,
                "grade_cells_dict": {
                    "cell-81540a070d18c412": {
                        "_type": "GradeCell",
                        "cell_type": "code",
                        "comment_id": None,
                        "grade_id": None,
                        "id": None,
                        "max_score": 1.0,
                        "name": "cell-81540a070d18c412",
                        "notebook_id": None,
                    },
                    "cell-9ea0264ada6c25bd": {
                        "_type": "GradeCell",
                        "cell_type": "markdown",
                        "comment_id": None,
                        "grade_id": None,
                        "id": None,
                        "max_score": 2.0,
                        "name": "cell-9ea0264ada6c25bd",
                        "notebook_id": None,
                    },
                    "cell-da8c82e850a1922b": {
                        "_type": "GradeCell",
                        "cell_type": "code",
                        "comment_id": None,
                        "grade_id": None,
                        "id": None,
                        "max_score": 1.0,
                        "name": "cell-da8c82e850a1922b",
                        "notebook_id": None,
                    },
                },
                "grades_dict": {},
                "id": "a5",
                "kernelspec": '{"display_name": "Python 3", "language": "python", "name": "python3"}',
                "name": "a5",
                "solution_cells_dict": {
                    "cell-28df1799f8f8b769": {
                        "_type": "SolutionCell",
                        "comment_id": None,
                        "grade_id": None,
                        "id": None,
                        "name": "cell-28df1799f8f8b769",
                        "notebook_id": None,
                    },
                    "cell-9ea0264ada6c25bd": {
                        "_type": "SolutionCell",
                        "comment_id": None,
                        "grade_id": None,
                        "id": None,
                        "name": "cell-9ea0264ada6c25bd",
                        "notebook_id": None,
                    },
                },
                "source_cells_dict": {
                    "cell-1b9d18df2b17e57f": {
                        "_type": "SourceCell",
                        "cell_type": "markdown",
                        "checksum": "92c710dde448a453c67a457a1a516266",
                        "id": None,
                        "locked": None,
                        "name": "cell-1b9d18df2b17e57f",
                        "notebook_id": None,
                        "source": '## Aufgabe 3\nDoes Java use "fake"-threads? Explain why or why not?',
                    },
                    "cell-26053a7da067ded3": {
                        "_type": "SourceCell",
                        "cell_type": "markdown",
                        "checksum": "341dd0694041ff4b5666c5ae94083cb4",
                        "id": None,
                        "locked": True,
                        "name": "cell-26053a7da067ded3",
                        "notebook_id": None,
                        "source": "### Aufgabe 1",
                    },
                    "cell-28df1799f8f8b769": {
                        "_type": "SourceCell",
                        "cell_type": "code",
                        "checksum": "bd34afadfba8f9e585d1245ca8d75beb",
                        "id": None,
                        "locked": False,
                        "name": "cell-28df1799f8f8b769",
                        "notebook_id": None,
                        "source": "def reverse(s):\n    # YOUR CODE HERE\n    raise NotImplementedError()",
                    },
                    "cell-81540a070d18c412": {
                        "_type": "SourceCell",
                        "cell_type": "code",
                        "checksum": "efff0d4fdfcbd070c4a9afa0afc914dc",
                        "id": None,
                        "locked": True,
                        "name": "cell-81540a070d18c412",
                        "notebook_id": None,
                        "source": "assert (reverse('lol') == 'lol')",
                    },
                    "cell-9ea0264ada6c25bd": {
                        "_type": "SourceCell",
                        "cell_type": "markdown",
                        "checksum": "cbcb81d7877ddde960682872f59d9578",
                        "id": None,
                        "locked": False,
                        "name": "cell-9ea0264ada6c25bd",
                        "notebook_id": None,
                        "source": "YOUR ANSWER HERE",
                    },
                    "cell-c06c761f0b7b0f59": {
                        "_type": "SourceCell",
                        "cell_type": "code",
                        "checksum": "4ce43bbad8e68a85ba3a7594ea9a41be",
                        "id": None,
                        "locked": True,
                        "name": "cell-c06c761f0b7b0f59",
                        "notebook_id": None,
                        "source": "reverse('Test')",
                    },
                    "cell-da8c82e850a1922b": {
                        "_type": "SourceCell",
                        "cell_type": "code",
                        "checksum": "5e838f105bec52e51e488e029e4727fd",
                        "id": None,
                        "locked": True,
                        "name": "cell-da8c82e850a1922b",
                        "notebook_id": None,
                        "source": "assert (reverse('Test') == 'tseT')",
                    },
                },
                "task_cells_dict": {},
            }
        },
        "schema_version": "1",
    }
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="PUT",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(prop),
        )
    e = exc_info.value
    assert e.code == HTTPStatus.CONFLICT
