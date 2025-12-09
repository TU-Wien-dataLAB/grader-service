# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
import json
from http import HTTPStatus
from pathlib import Path

import pytest
from sqlalchemy.orm import Session, sessionmaker
from tornado.httpclient import HTTPClientError

from grader_service.api.models.assignment import Assignment
from grader_service.api.models.assignment_settings import AssignmentSettings
from grader_service.api.models.lecture import Lecture
from grader_service.server import GraderServer

from ... import orm
from ...handlers import GitRepoType
from ...orm.base import DeleteState
from .db_util import (
    create_git_repository,
    insert_assignment,
    insert_assignments,
    insert_student,
    insert_submission,
)


async def test_get_lectures(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
):
    url = service_base_url + "lectures"

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK
    lectures = json.loads(response.body.decode())
    assert isinstance(lectures, list)
    assert lectures
    [Lecture.from_dict(lec) for lec in lectures]  # assert no errors
    assert len(lectures) == 3


async def test_get_lectures_admin(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_admin_login,
):
    url = service_base_url + "lectures"

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK
    lectures = json.loads(response.body.decode())
    assert isinstance(lectures, list)
    assert lectures
    [Lecture.from_dict(lec) for lec in lectures]
    assert len(lectures) == 4


async def test_get_lectures_with_some_parameter(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    default_roles,
    default_user_login,
):
    url = service_base_url + "lectures?some_param=WS21"
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.BAD_REQUEST


async def test_post_lectures_update(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    default_roles,
    default_user_login,
):
    url = service_base_url + "lectures"

    get_response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert get_response.code == HTTPStatus.OK
    lectures = json.loads(get_response.body.decode())
    assert isinstance(lectures, list)
    assert len(lectures) == 3
    orig_len = len(lectures)

    # same code as in group of user
    pre_lecture = Lecture(id=-1, name="pytest_lecture", code="20wle2", complete=False)
    post_response = await http_server_client.fetch(
        url,
        method="POST",
        headers={"Authorization": f"Token {default_token}"},
        body=json.dumps(pre_lecture.to_dict()),
    )
    assert post_response.code == HTTPStatus.CREATED
    post_lecture = Lecture.from_dict(json.loads(post_response.body.decode()))
    assert post_lecture.id != pre_lecture.id
    assert post_lecture.name == pre_lecture.name
    assert post_lecture.code == pre_lecture.code
    assert not post_lecture.complete

    get_response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert get_response.code == HTTPStatus.OK
    lectures = json.loads(get_response.body.decode())
    assert len(lectures) == orig_len


async def test_post_lectures_update_unauthorized(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    default_roles,
    default_user_login,
):
    url = service_base_url + "lectures"

    pre_lecture = Lecture(id=-1, name="pytest_lecture", code="23wle1", complete=False)
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="POST",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(pre_lecture.to_dict()),
        )

    e = exc_info.value
    assert e.code == HTTPStatus.FORBIDDEN


async def test_post_lectures_update_admin(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_admin,
    default_token,
    default_roles,
    default_admin_login,
):
    url = service_base_url + "lectures"

    get_response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert get_response.code == HTTPStatus.OK
    lectures = json.loads(get_response.body.decode())
    assert isinstance(lectures, list)
    assert len(lectures) == 4
    orig_len = len(lectures)

    # same code as in group of user
    pre_lecture = Lecture(id=-1, name="pytest_lecture", code="21wle1", complete=False)
    post_response = await http_server_client.fetch(
        url,
        method="POST",
        headers={"Authorization": f"Token {default_token}"},
        body=json.dumps(pre_lecture.to_dict()),
    )
    assert post_response.code == HTTPStatus.CREATED
    post_lecture = Lecture.from_dict(json.loads(post_response.body.decode()))
    assert post_lecture.id != pre_lecture.id
    assert post_lecture.name == pre_lecture.name
    assert post_lecture.code == pre_lecture.code
    assert not post_lecture.complete

    get_response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert get_response.code == HTTPStatus.OK
    lectures = json.loads(get_response.body.decode())
    assert len(lectures) == orig_len


async def test_post_lectures_new_unauthorized(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    default_roles,
    default_user_login,
):
    url = service_base_url + "lectures"

    pre_lecture = Lecture(id=-1, name="pytest_lecture_new", code="abc", complete=False)
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="POST",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(pre_lecture.to_dict()),
        )

    e = exc_info.value
    assert e.code == HTTPStatus.FORBIDDEN


async def test_post_lectures_new_admin(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_admin,
    default_token,
    default_roles,
    default_admin_login,
):
    url = service_base_url + "lectures"

    get_response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert get_response.code == HTTPStatus.OK
    lectures = json.loads(get_response.body.decode())
    assert isinstance(lectures, list)
    assert len(lectures) == 4
    orig_len = len(lectures)

    # same code as in group of user
    pre_lecture = Lecture(id=-1, name="pytest_lecture", code="abc", complete=False)
    post_response = await http_server_client.fetch(
        url,
        method="POST",
        headers={"Authorization": f"Token {default_token}"},
        body=json.dumps(pre_lecture.to_dict()),
    )
    assert post_response.code == HTTPStatus.CREATED
    post_lecture = Lecture.from_dict(json.loads(post_response.body.decode()))
    assert post_lecture.id != pre_lecture.id
    assert post_lecture.name == pre_lecture.name
    assert post_lecture.code == pre_lecture.code
    assert not post_lecture.complete

    get_response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert get_response.code == HTTPStatus.OK
    lectures = json.loads(get_response.body.decode())
    assert len(lectures) == orig_len + 1


async def test_post_unknown_parameter(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    default_roles,
    default_user_login,
):
    url = service_base_url + "lectures?some_param=asdf"
    # same code not in user groups
    pre_lecture = Lecture(id=-1, name="pytest_lecture", code="20wle2", complete=False)
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="POST",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(pre_lecture.to_dict()),
        )
    e = exc_info.value
    assert e.code == HTTPStatus.BAD_REQUEST


async def test_put_lecture(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    default_roles,
    default_user_login,
):
    url = service_base_url + "lectures/3"

    get_response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert get_response.code == HTTPStatus.OK
    lecture = Lecture.from_dict(json.loads(get_response.body.decode()))
    lecture.name = "new name"
    lecture.complete = not lecture.complete
    # lecture code will not be updated
    lecture.code = "some"

    put_response = await http_server_client.fetch(
        url,
        method="PUT",
        headers={"Authorization": f"Token {default_token}"},
        body=json.dumps(lecture.to_dict()),
    )

    assert put_response.code == HTTPStatus.OK
    put_lecture = Lecture.from_dict(json.loads(put_response.body.decode()))
    assert put_lecture.name == lecture.name
    assert put_lecture.complete == lecture.complete
    assert put_lecture.code != lecture.code


async def test_put_lecture_unauthorized(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
):
    #  default user is a student in lecture with lecture_id 1
    url = service_base_url + "lectures/1"

    get_response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert get_response.code == HTTPStatus.OK
    lecture = Lecture.from_dict(json.loads(get_response.body.decode()))
    lecture.name = "new name"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="PUT",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(lecture.to_dict()),
        )

    e = exc_info.value
    assert e.code == HTTPStatus.FORBIDDEN


async def test_get_lecture(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
):
    url = service_base_url + "lectures/1"

    get_response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert get_response.code == HTTPStatus.OK
    Lecture.from_dict(json.loads(get_response.body.decode()))


async def test_get_lecture_unauthorized(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
):
    url = service_base_url + "lectures/999"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.FORBIDDEN


async def test_get_lecture_admin_not_found(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_admin_login,
):
    url = service_base_url + "lectures/999"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND


async def test_get_lecture_admin(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_admin_login,
):
    url = service_base_url + "lectures/1"

    get_response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert get_response.code == HTTPStatus.OK
    Lecture.from_dict(json.loads(get_response.body.decode()))


async def test_delete_lecture(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
    sql_alchemy_engine,
):
    l_id = 3
    url = service_base_url + f"lectures/{l_id}"

    delete_response = await http_server_client.fetch(
        url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
    )
    assert delete_response.code == HTTPStatus.OK

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND

    session: Session = sessionmaker(sql_alchemy_engine)()
    lectures = session.query(orm.Lecture).filter(orm.Lecture.id == l_id).all()
    assert len(lectures) == 1
    assert lectures[0].deleted == DeleteState.deleted


async def test_delete_lecture_already_deleted(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
):
    url = service_base_url + "lectures/3"

    delete_response = await http_server_client.fetch(
        url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
    )
    assert delete_response.code == HTTPStatus.OK

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND


async def test_delete_lecture_unauthorized(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
):
    url = service_base_url + "lectures/1"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.FORBIDDEN


async def test_delete_lecture_assignment(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
    default_user,
):
    l_id = 3
    a_id = 3
    url = service_base_url + f"lectures/{l_id}"

    engine = sql_alchemy_engine
    insert_assignment(engine, lecture_id=l_id)

    delete_response = await http_server_client.fetch(
        url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
    )
    assert delete_response.code == HTTPStatus.OK

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND

    url = service_base_url + f"lectures/{l_id}/assignments/{a_id}"
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND

    session: Session = sessionmaker(sql_alchemy_engine)()
    lectures = session.query(orm.Lecture).filter(orm.Lecture.id == l_id).all()
    assert len(lectures) == 1
    assert lectures[0].deleted == DeleteState.deleted

    session: Session = sessionmaker(sql_alchemy_engine)()
    assignments = session.query(orm.Assignment).filter(orm.Assignment.lectid == l_id).all()
    assert len(assignments) == 1
    assert assignments[0].deleted == DeleteState.deleted


async def test_delete_lecture_assignment_with_submissions(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
    default_user,
):
    l_id = 3
    a_id = 3
    url = service_base_url + f"lectures/{l_id}"

    engine = sql_alchemy_engine
    insert_assignment(engine, lecture_id=l_id)
    insert_submission(engine, a_id, default_user.name, default_user.id)

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.CONFLICT


async def test_delete_lecture_assignment_released(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = 3
    url = service_base_url + f"lectures/{l_id}"

    engine = sql_alchemy_engine
    insert_assignments(engine, lecture_id=3)  # assignment with id 1 is status released

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.CONFLICT


async def test_delete_lecture_assignment_complete(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
):
    l_id = 3
    url = service_base_url + f"lectures/{l_id}/assignments"

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

    url = service_base_url + f"lectures/{l_id}"
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.CONFLICT


async def test_delete_lecture_not_found(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
):
    l_id = -5

    url = service_base_url + f"lectures/{l_id}"
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND


async def test_delete_lecture_hard(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_admin_login,
    sql_alchemy_engine,
):
    l_id = 3

    url = service_base_url + f"lectures/{l_id}"
    delete_response = await http_server_client.fetch(
        url + "?hard_delete=true",
        method="DELETE",
        headers={"Authorization": f"Token {default_token}"},
    )
    assert delete_response.code == HTTPStatus.OK

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND

    session: Session = sessionmaker(sql_alchemy_engine)()
    lectures = session.query(orm.Lecture).filter(orm.Lecture.id == l_id).all()
    assert len(lectures) == 0


async def test_delete_lecture_hard_unauthorized(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
    sql_alchemy_engine,
):
    l_id = 3

    url = service_base_url + f"lectures/{l_id}"
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url + "?hard_delete=true",
            method="DELETE",
            headers={"Authorization": f"Token {default_token}"},
        )
    e = exc_info.value
    assert e.code == HTTPStatus.FORBIDDEN


async def test_delete_lecture_hard_assignments_roles(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_admin_login,
    sql_alchemy_engine,
    default_admin,
):
    l_id = 4
    l_code = "23wle1"
    a_id = 3

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

    create_git_repository(
        app=app,
        l_id=l_id,
        code=l_code,
        a_id=a_id,
        s_id=1,
        repo_type=GitRepoType.SOURCE,
        username=default_admin.name,
    )

    git_dir = Path(app.grader_service_dir) / "git" / l_code / str(a_id)
    assert git_dir.exists()

    url = service_base_url + f"lectures/{l_id}"
    delete_response = await http_server_client.fetch(
        url + "?hard_delete=true",
        method="DELETE",
        headers={"Authorization": f"Token {default_token}"},
    )
    assert delete_response.code == HTTPStatus.OK

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND

    session: Session = sessionmaker(sql_alchemy_engine)()
    lectures = session.query(orm.Lecture).filter(orm.Lecture.id == l_id).all()
    assert len(lectures) == 0

    assignments = session.query(orm.Assignment).filter(orm.Assignment.lectid == l_id).all()
    assert len(assignments) == 0

    roles = session.query(orm.Role).filter(orm.Role.lectid == l_id).all()
    assert len(roles) == 0

    assert not git_dir.exists()


async def test_delete_lecture_unknown_parameter(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    default_roles,
    default_user_login,
):
    l_id = 3

    url = service_base_url + f"lectures/{l_id}?some_param=asdf"
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.BAD_REQUEST


async def test_get_lecture_users(
    service_base_url,
    http_server_client,
    default_token,
    sql_alchemy_engine,
    default_roles,
    default_user_login,
    default_user,
):
    l_id = 3
    insert_student(sql_alchemy_engine, "student1", l_id)
    insert_student(sql_alchemy_engine, "student2", l_id)

    url = service_base_url + f"lectures/{l_id}/users"
    resp = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )

    assert resp.code == HTTPStatus.OK
    data = json.loads(resp.body.decode())
    assert data["instructors"] == [
        {"id": 1, "name": default_user.name, "display_name": default_user.display_name}
    ]
    assert data["tutors"] == []
    assert data["students"] == [
        {"id": 2, "name": "student1", "display_name": "student1"},
        {"id": 3, "name": "student2", "display_name": "student2"},
    ]
