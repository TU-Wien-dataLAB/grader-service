# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
import json
from datetime import UTC, datetime
from http import HTTPStatus
from pathlib import Path

import pytest
from sqlalchemy.orm import Session, sessionmaker
from tornado.httpclient import HTTPClientError

from grader_service import orm
from grader_service.api.models.assignment import Assignment
from grader_service.api.models.assignment_settings import AssignmentSettings
from grader_service.api.models.lecture import Lecture
from grader_service.artifact_types import ArtifactType
from grader_service.orm.base import DeleteState
from grader_service.orm.lecture import LectureState
from grader_service.orm.takepart import Scope
from grader_service.server import GraderServer

from .db_util import (
    add_role,
    create_git_repository,
    insert_assignment,
    insert_assignments,
    insert_student,
    insert_submission,
)
from ...api.models import LectureListItemDto, LectureDetailDto, LectureUpdateDto


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
    data = json.loads(response.body.decode())
    lectures = data["lectures"]
    assert isinstance(lectures, list)
    assert lectures
    [LectureListItemDto.from_dict(lec) for lec in lectures]  # assert no errors
    assert len(lectures) == 3
    assert data["page"] == 1
    assert data["per_page"] == 20
    assert data["total_items"] == 3
    assert data["total_pages"] == 1


async def test_get_lectures_complete(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
    default_user,
    sql_alchemy_engine,
):
    url = service_base_url + "lectures?complete=true"

    session: Session = sessionmaker(sql_alchemy_engine)()
    session.add(
        orm.Lecture(
            id=10, name="test", code="test", state=LectureState.complete, deleted=DeleteState.active
        )
    )
    session.add(
        orm.Lecture(
            id=11,
            name="test2",
            code="test2",
            state=LectureState.complete,
            deleted=DeleteState.deleted,
        )
    )
    session.commit()

    add_role(sql_alchemy_engine, default_user.id, 10, Scope.instructor)
    add_role(sql_alchemy_engine, default_user.id, 11, Scope.instructor)

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK
    data = json.loads(response.body.decode())
    lectures = data["lectures"]
    assert isinstance(lectures, list)
    assert lectures
    [Lecture.from_dict(lec) for lec in lectures]  # assert no errors
    assert len(lectures) == 1


async def test_get_lectures_instructor(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
    default_user,
    sql_alchemy_engine,
):
    url = service_base_url + "lectures?instructor=true"

    session: Session = sessionmaker(sql_alchemy_engine)()
    session.add(
        orm.Lecture(
            id=10, name="test", code="test", state=LectureState.active, deleted=DeleteState.active
        )
    )
    session.add(
        orm.Lecture(
            id=11, name="test2", code="test2", state=LectureState.active, deleted=DeleteState.active
        )
    )
    session.commit()

    add_role(sql_alchemy_engine, default_user.id, 10, Scope.student)
    add_role(sql_alchemy_engine, default_user.id, 11, Scope.instructor)

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK
    data = json.loads(response.body.decode())
    lectures = data["lectures"]
    assert isinstance(lectures, list)
    assert lectures
    [Lecture.from_dict(lec) for lec in lectures]  # assert no errors
    assert len(lectures) == 3
    assert lectures[0]["id"] == 2
    assert lectures[1]["id"] == 3
    assert lectures[2]["id"] == 11


async def test_get_lectures_instructor_and_complete(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
    default_user,
    sql_alchemy_engine,
):
    url = service_base_url + "lectures?complete=true&instructor=true"

    session: Session = sessionmaker(sql_alchemy_engine)()
    session.add(
        orm.Lecture(
            id=10, name="test", code="test", state=LectureState.complete, deleted=DeleteState.active
        )
    )
    session.add(
        orm.Lecture(
            id=11,
            name="test2",
            code="test2",
            state=LectureState.complete,
            deleted=DeleteState.active,
        )
    )
    session.commit()

    add_role(sql_alchemy_engine, default_user.id, 10, Scope.student)
    add_role(sql_alchemy_engine, default_user.id, 11, Scope.instructor)

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK
    data = json.loads(response.body.decode())
    lectures = data["lectures"]
    assert isinstance(lectures, list)
    assert lectures
    [Lecture.from_dict(lec) for lec in lectures]  # assert no errors
    assert len(lectures) == 1
    assert lectures[0]["id"] == 11


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
    data = json.loads(response.body.decode())
    lectures = data["lectures"]
    assert isinstance(lectures, list)
    assert lectures
    [Lecture.from_dict(lec) for lec in lectures]
    assert len(lectures) == 4
    assert data["page"] == 1
    assert data["per_page"] == 20
    assert data["total_items"] == 4
    assert data["total_pages"] == 1


async def test_get_lectures_admin_complete(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_admin_login,
    sql_alchemy_engine,
):
    url = service_base_url + "lectures?complete=true"

    session: Session = sessionmaker(sql_alchemy_engine)()
    session.add(
        orm.Lecture(
            id=10, name="test", code="test", state=LectureState.complete, deleted=DeleteState.active
        )
    )
    session.add(
        orm.Lecture(
            id=11,
            name="test2",
            code="test2",
            state=LectureState.complete,
            deleted=DeleteState.deleted,
        )
    )
    session.commit()

    response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert response.code == HTTPStatus.OK
    data = json.loads(response.body.decode())
    lectures = data["lectures"]
    assert isinstance(lectures, list)
    assert lectures
    [Lecture.from_dict(lec) for lec in lectures]
    assert len(lectures) == 2


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


async def test_get_lectures_default_pagination(
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
    data = json.loads(response.body.decode())
    assert data["page"] == 1
    assert data["per_page"] == 20
    assert data["total_items"] == 3
    assert data["total_pages"] == 1
    assert len(data["lectures"]) == 3


async def test_get_lectures_pagination_paging(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
):
    # default user sees lectures 1, 2 and 3
    page_1 = await http_server_client.fetch(
        service_base_url + "lectures?page=1&per_page=2",
        method="GET",
        headers={"Authorization": f"Token {default_token}"},
    )
    assert page_1.code == HTTPStatus.OK
    data = json.loads(page_1.body.decode())
    assert data["page"] == 1
    assert data["per_page"] == 2
    assert data["total_items"] == 3
    assert data["total_pages"] == 2
    assert [lec["id"] for lec in data["lectures"]] == [1, 2]

    page_2 = await http_server_client.fetch(
        service_base_url + "lectures?page=2&per_page=2",
        method="GET",
        headers={"Authorization": f"Token {default_token}"},
    )
    assert page_2.code == HTTPStatus.OK
    data = json.loads(page_2.body.decode())
    assert data["page"] == 2
    assert data["per_page"] == 2
    assert data["total_items"] == 3
    assert data["total_pages"] == 2
    assert [lec["id"] for lec in data["lectures"]] == [3]

    page_3 = await http_server_client.fetch(
        service_base_url + "lectures?page=3&per_page=2",
        method="GET",
        headers={"Authorization": f"Token {default_token}"},
    )
    assert page_3.code == HTTPStatus.OK
    data = json.loads(page_3.body.decode())
    assert data["page"] == 3
    assert data["per_page"] == 2
    assert data["total_items"] == 3
    assert data["total_pages"] == 2
    assert data["lectures"] == []


async def test_get_lectures_page_beyond_range(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
):
    response = await http_server_client.fetch(
        service_base_url + "lectures?page=99&per_page=2",
        method="GET",
        headers={"Authorization": f"Token {default_token}"},
    )
    assert response.code == HTTPStatus.OK
    data = json.loads(response.body.decode())
    assert data["page"] == 99
    assert data["per_page"] == 2
    assert data["total_items"] == 3
    assert data["total_pages"] == 2
    assert data["lectures"] == []


async def test_get_lectures_sort_by_id(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
):
    response = await http_server_client.fetch(
        service_base_url + "lectures?sort_by=id&order=asc",
        method="GET",
        headers={"Authorization": f"Token {default_token}"},
    )
    assert response.code == HTTPStatus.OK
    data = json.loads(response.body.decode())
    assert [lec["id"] for lec in data["lectures"]] == [1, 2, 3]

    response = await http_server_client.fetch(
        service_base_url + "lectures?sort_by=id&order=desc",
        method="GET",
        headers={"Authorization": f"Token {default_token}"},
    )
    assert response.code == HTTPStatus.OK
    data = json.loads(response.body.decode())
    assert [lec["id"] for lec in data["lectures"]] == [3, 2, 1]


async def test_get_lectures_sort_by_name(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
    default_user,
    sql_alchemy_engine,
):
    session: Session = sessionmaker(sql_alchemy_engine)()
    session.add(
        orm.Lecture(
            id=10,
            name="a_lecture",
            code="a_lecture",
            state=LectureState.active,
            deleted=DeleteState.active,
        )
    )
    session.commit()
    add_role(sql_alchemy_engine, default_user.id, 10, Scope.student)

    response = await http_server_client.fetch(
        service_base_url + "lectures?sort_by=name&order=asc",
        method="GET",
        headers={"Authorization": f"Token {default_token}"},
    )
    assert response.code == HTTPStatus.OK
    data = json.loads(response.body.decode())
    assert [lec["name"] for lec in data["lectures"]] == [
        "a_lecture",
        "lecture1",
        "lecture2",
        "lecture3",
    ]

    response = await http_server_client.fetch(
        service_base_url + "lectures?sort_by=name&order=desc",
        method="GET",
        headers={"Authorization": f"Token {default_token}"},
    )
    assert response.code == HTTPStatus.OK
    data = json.loads(response.body.decode())
    assert [lec["name"] for lec in data["lectures"]] == [
        "lecture3",
        "lecture2",
        "lecture1",
        "a_lecture",
    ]


async def test_get_lectures_sort_by_created_at(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
    default_user,
    sql_alchemy_engine,
):
    # the lectures from the fixtures all have essentially the same created_at
    # (column default), so we insert lectures with explicit and distinct
    # created_at values to test date sorting deterministically
    session: Session = sessionmaker(sql_alchemy_engine)()
    session.add(
        orm.Lecture(
            id=20,
            name="oldest",
            code="c20",
            state=LectureState.active,
            deleted=DeleteState.active,
            created_at=datetime(2020, 1, 1, tzinfo=UTC),
        )
    )
    session.add(
        orm.Lecture(
            id=21,
            name="mid_a",
            code="c21",
            state=LectureState.active,
            deleted=DeleteState.active,
            created_at=datetime(2021, 1, 1, tzinfo=UTC),
        )
    )
    # same created_at as lecture 21 -> id is used as tiebreaker
    session.add(
        orm.Lecture(
            id=22,
            name="mid_b",
            code="c22",
            state=LectureState.active,
            deleted=DeleteState.active,
            created_at=datetime(2021, 1, 1, tzinfo=UTC),
        )
    )
    session.add(
        orm.Lecture(
            id=23,
            name="newest",
            code="c23",
            state=LectureState.active,
            deleted=DeleteState.active,
            created_at=datetime(2022, 1, 1, tzinfo=UTC),
        )
    )
    session.commit()

    for l_id in (20, 21, 22, 23):
        add_role(sql_alchemy_engine, default_user.id, l_id, Scope.student)

    response = await http_server_client.fetch(
        service_base_url + "lectures?sort_by=created_at&order=asc&per_page=100",
        method="GET",
        headers={"Authorization": f"Token {default_token}"},
    )
    assert response.code == HTTPStatus.OK
    data = json.loads(response.body.decode())
    # fixture lectures (ids 1-3) have the newest created_at and are tied,
    # so they are ordered by id; 21 and 22 are tied and ordered by id
    assert [lec["id"] for lec in data["lectures"]] == [20, 21, 22, 23, 1, 2, 3]

    response = await http_server_client.fetch(
        service_base_url + "lectures?sort_by=created_at&order=desc&per_page=100",
        method="GET",
        headers={"Authorization": f"Token {default_token}"},
    )
    assert response.code == HTTPStatus.OK
    data = json.loads(response.body.decode())
    # descending: tied lectures are ordered by id descending
    assert [lec["id"] for lec in data["lectures"]] == [3, 2, 1, 23, 22, 21, 20]


async def test_get_lectures_invalid_query_params(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
):
    invalid_queries = [
        "page=0",
        "page=abc",
        "page=-1",
        "per_page=0",
        "per_page=101",
        "per_page=abc",
        "sort_by=foo",
        "order=up",
        "complete=yes",
        "instructor=1",
        "instructor=TRUE",
    ]
    for query in invalid_queries:
        url = service_base_url + "lectures?" + query
        with pytest.raises(HTTPClientError) as exc_info:
            await http_server_client.fetch(
                url, method="GET", headers={"Authorization": f"Token {default_token}"}
            )
        e = exc_info.value
        assert e.code == HTTPStatus.BAD_REQUEST, f"query '{query}' did not return 400"


async def test_get_lectures_complete_with_pagination(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
    default_user,
    sql_alchemy_engine,
):
    session: Session = sessionmaker(sql_alchemy_engine)()
    session.add(
        orm.Lecture(
            id=30,
            name="complete_1",
            code="c30",
            state=LectureState.complete,
            deleted=DeleteState.active,
        )
    )
    session.add(
        orm.Lecture(
            id=31,
            name="complete_2",
            code="c31",
            state=LectureState.complete,
            deleted=DeleteState.active,
        )
    )
    session.commit()

    add_role(sql_alchemy_engine, default_user.id, 30, Scope.instructor)
    add_role(sql_alchemy_engine, default_user.id, 31, Scope.instructor)

    response = await http_server_client.fetch(
        service_base_url + "lectures?complete=true&per_page=1&page=2",
        method="GET",
        headers={"Authorization": f"Token {default_token}"},
    )
    assert response.code == HTTPStatus.OK
    data = json.loads(response.body.decode())
    # only the two complete lectures match the filter
    assert data["page"] == 2
    assert data["per_page"] == 1
    assert data["total_items"] == 2
    assert data["total_pages"] == 2
    assert [lec["id"] for lec in data["lectures"]] == [31]


async def test_post_lecture_existing_code(
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
    lectures = json.loads(get_response.body.decode())["lectures"]
    assert isinstance(lectures, list)
    assert len(lectures) == 3
    name_before = next(lec["name"] for lec in lectures if lec["code"] == "20wle2")

    # creating a lecture with an already existing lecture code is rejected
    pre_lecture = Lecture(id=-1, name="pytest_lecture", code="20wle2", complete=False)
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="POST",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(pre_lecture.to_dict()),
        )
    e = exc_info.value
    assert e.code == HTTPStatus.CONFLICT

    get_response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert get_response.code == HTTPStatus.OK
    lectures = json.loads(get_response.body.decode())["lectures"]
    assert len(lectures) == 3
    assert next(lec["name"] for lec in lectures if lec["code"] == "20wle2") == name_before


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


async def test_post_lecture_existing_code_admin(
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
    lectures = json.loads(get_response.body.decode())["lectures"]
    assert isinstance(lectures, list)
    assert len(lectures) == 4
    name_before = next(lec["name"] for lec in lectures if lec["code"] == "21wle1")

    # creating a lecture with an already existing lecture code is rejected
    pre_lecture = Lecture(id=-1, name="pytest_lecture", code="21wle1", complete=False)
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="POST",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(pre_lecture.to_dict()),
        )
    e = exc_info.value
    assert e.code == HTTPStatus.CONFLICT

    get_response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert get_response.code == HTTPStatus.OK
    lectures = json.loads(get_response.body.decode())["lectures"]
    assert len(lectures) == 4
    assert next(lec["name"] for lec in lectures if lec["code"] == "21wle1") == name_before


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
    data = json.loads(get_response.body.decode())
    lectures = data["lectures"]
    assert isinstance(lectures, list)
    assert len(lectures) == 4
    orig_len = data["total_items"]

    # create new lecture
    pre_lecture = Lecture(id=-1, name="pytest_lecture", code="abc", complete=False)
    post_response = await http_server_client.fetch(
        url,
        method="POST",
        headers={"Authorization": f"Token {default_token}"},
        body=json.dumps(pre_lecture.to_dict()),
    )
    assert post_response.code == HTTPStatus.CREATED
    post_lecture = LectureDetailDto.from_dict(json.loads(post_response.body.decode()))
    assert post_lecture.name == pre_lecture.name
    assert post_lecture.code == pre_lecture.code
    assert not post_lecture.complete

    get_response = await http_server_client.fetch(
        url, method="GET", headers={"Authorization": f"Token {default_token}"}
    )
    assert get_response.code == HTTPStatus.OK
    data = json.loads(get_response.body.decode())
    lectures = data["lectures"]
    assert len(lectures) == orig_len + 1
    assert data["total_items"] == orig_len + 1


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
    lecture = LectureDetailDto.from_dict(json.loads(get_response.body.decode()))
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
    lecture = LectureDetailDto.from_dict(json.loads(get_response.body.decode()))
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


async def test_put_lecture_deleted(
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
    assert delete_response.code == HTTPStatus.NO_CONTENT

    update_lecture = LectureUpdateDto(name="new name", complete=False)

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="PUT",
            headers={"Authorization": f"Token {default_token}"},
            body=json.dumps(update_lecture.to_dict()),
        )
    e = exc_info.value
    assert e.code == HTTPStatus.NOT_FOUND


async def test_put_lecture_deleted_admin(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_admin,
    default_token,
    default_roles,
    default_admin_login,
):
    # admins keep access to deleted lectures, so updates must still work
    url = service_base_url + "lectures/3"

    delete_response = await http_server_client.fetch(
        url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
    )
    assert delete_response.code == HTTPStatus.NO_CONTENT

    update_lecture = LectureUpdateDto(name="new name", complete=False)
    put_response = await http_server_client.fetch(
        url,
        method="PUT",
        headers={"Authorization": f"Token {default_token}"},
        body=json.dumps(update_lecture.to_dict()),
    )
    assert put_response.code == HTTPStatus.OK
    updated = LectureDetailDto.from_dict(json.loads(put_response.body.decode()))
    assert updated.name == "new name"


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
    assert delete_response.code == HTTPStatus.NO_CONTENT

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
    assert delete_response.code == HTTPStatus.NO_CONTENT

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
    assert delete_response.code == HTTPStatus.NO_CONTENT

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
        settings=AssignmentSettings(grading_method="manual"),
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
    assert delete_response.code == HTTPStatus.NO_CONTENT

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
        l_code=l_code,
        a_id=a_id,
        artifact_type=ArtifactType.SOURCE,
        s_id=1,
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
    assert delete_response.code == HTTPStatus.NO_CONTENT

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


async def test_delete_lecture_invalid_hard_delete_value(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    default_roles,
    default_user_login,
):
    url = service_base_url + "lectures/3?hard_delete=yes"
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url, method="DELETE", headers={"Authorization": f"Token {default_token}"}
        )
    e = exc_info.value
    assert e.code == HTTPStatus.BAD_REQUEST


async def test_post_lecture_invalid_body(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_admin,
    default_token,
    default_roles,
    default_admin_login,
):
    url = service_base_url + "lectures"

    # not valid JSON
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="POST",
            headers={"Authorization": f"Token {default_token}"},
            body="{invalid json",
        )
    e = exc_info.value
    assert e.code == HTTPStatus.BAD_REQUEST

    # JSON, but the body is not an object
    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="POST",
            headers={"Authorization": f"Token {default_token}"},
            body="[1, 2, 3]",
        )
    e = exc_info.value
    assert e.code == HTTPStatus.BAD_REQUEST


async def test_put_lecture_invalid_body(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_user,
    default_token,
    default_roles,
    default_user_login,
):
    url = service_base_url + "lectures/3"

    with pytest.raises(HTTPClientError) as exc_info:
        await http_server_client.fetch(
            url,
            method="PUT",
            headers={"Authorization": f"Token {default_token}"},
            body="not json at all",
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
        {"id": 3, "name": "student1", "display_name": "student1"},
        {"id": 4, "name": "student2", "display_name": "student2"},
    ]


async def test_get_lectures_search_by_name(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
):
    # default user sees lectures 1, 2 and 3; only lecture2 contains "lecture2"
    response = await http_server_client.fetch(
        service_base_url + "lectures?search=lecture2",
        method="GET",
        headers={"Authorization": f"Token {default_token}"},
    )
    assert response.code == HTTPStatus.OK
    data = json.loads(response.body.decode())
    lectures = data["lectures"]
    assert isinstance(lectures, list)
    [LectureListItemDto.from_dict(lec) for lec in lectures]  # assert no errors
    assert len(lectures) == 1
    assert lectures[0]["name"] == "lecture2"
    assert lectures[0]["id"] == 2
    assert data["page"] == 1
    assert data["per_page"] == 20
    assert data["total_items"] == 1
    assert data["total_pages"] == 1


async def test_get_lectures_search_by_code(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
):
    # codes of the lectures visible to the default user: 21wle1, 20wle2, 22wle1
    # "wle1" matches the codes of lectures 1 and 3
    response = await http_server_client.fetch(
        service_base_url + "lectures?search=wle1",
        method="GET",
        headers={"Authorization": f"Token {default_token}"},
    )
    assert response.code == HTTPStatus.OK
    data = json.loads(response.body.decode())
    assert [lec["id"] for lec in data["lectures"]] == [1, 3]
    assert data["total_items"] == 2
    assert data["total_pages"] == 1

    # exact code match returns only lecture 2
    response = await http_server_client.fetch(
        service_base_url + "lectures?search=20wle2",
        method="GET",
        headers={"Authorization": f"Token {default_token}"},
    )
    assert response.code == HTTPStatus.OK
    data = json.loads(response.body.decode())
    assert [lec["id"] for lec in data["lectures"]] == [2]
    assert data["total_items"] == 1


async def test_get_lectures_search_case_insensitive(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
):
    response = await http_server_client.fetch(
        service_base_url + "lectures?search=LECTURE2",
        method="GET",
        headers={"Authorization": f"Token {default_token}"},
    )
    assert response.code == HTTPStatus.OK
    data = json.loads(response.body.decode())
    assert [lec["id"] for lec in data["lectures"]] == [2]
    assert data["total_items"] == 1

    # mixed casing on a lecture code
    response = await http_server_client.fetch(
        service_base_url + "lectures?search=20Wle2",
        method="GET",
        headers={"Authorization": f"Token {default_token}"},
    )
    assert response.code == HTTPStatus.OK
    data = json.loads(response.body.decode())
    assert [lec["id"] for lec in data["lectures"]] == [2]
    assert data["total_items"] == 1

    # upper case code fragment matches multiple lectures
    response = await http_server_client.fetch(
        service_base_url + "lectures?search=WLE1",
        method="GET",
        headers={"Authorization": f"Token {default_token}"},
    )
    assert response.code == HTTPStatus.OK
    data = json.loads(response.body.decode())
    assert [lec["id"] for lec in data["lectures"]] == [1, 3]
    assert data["total_items"] == 2


async def test_get_lectures_search_no_matches(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
):
    response = await http_server_client.fetch(
        service_base_url + "lectures?search=nomatch",
        method="GET",
        headers={"Authorization": f"Token {default_token}"},
    )
    assert response.code == HTTPStatus.OK
    data = json.loads(response.body.decode())
    assert data["lectures"] == []
    assert data["page"] == 1
    assert data["per_page"] == 20
    assert data["total_items"] == 0
    assert data["total_pages"] == 0


async def test_get_lectures_search_escapes_like_wildcards(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
    default_user,
    sql_alchemy_engine,
):
    # insert a lecture whose name contains a literal underscore;
    # the fixture lectures (lecture1..lecture4, 21wle1, ...) contain none
    session: Session = sessionmaker(sql_alchemy_engine)()
    session.add(
        orm.Lecture(
            id=40,
            name="test_lecture",
            code="40code",
            state=LectureState.active,
            deleted=DeleteState.active,
        )
    )
    session.commit()
    add_role(sql_alchemy_engine, default_user.id, 40, Scope.instructor)

    headers = {"Authorization": f"Token {default_token}"}

    # "_" must be matched literally: only the inserted lecture contains an
    # underscore (as a wildcard it would match every single character)
    response = await http_server_client.fetch(
        service_base_url + "lectures?search=_", method="GET", headers=headers
    )
    assert response.code == HTTPStatus.OK
    data = json.loads(response.body.decode())
    assert [lec["id"] for lec in data["lectures"]] == [40]
    assert data["total_items"] == 1

    # "%" must be matched literally: no name or code contains a percent sign
    # (as a wildcard it would match all lectures)
    response = await http_server_client.fetch(
        service_base_url + "lectures?search=%", method="GET", headers=headers
    )
    assert response.code == HTTPStatus.OK
    data = json.loads(response.body.decode())
    assert data["lectures"] == []
    assert data["total_items"] == 0
    assert data["total_pages"] == 0


async def test_get_lectures_search_with_pagination(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
    default_user,
    sql_alchemy_engine,
):
    # add a fourth lecture visible to the default user and matching "le"
    session: Session = sessionmaker(sql_alchemy_engine)()
    session.add(
        orm.Lecture(
            id=41,
            name="lecture41",
            code="41code",
            state=LectureState.active,
            deleted=DeleteState.active,
        )
    )
    session.commit()
    add_role(sql_alchemy_engine, default_user.id, 41, Scope.instructor)

    headers = {"Authorization": f"Token {default_token}"}

    # "le" matches all four visible lectures (names lecture1..lecture3, lecture41)
    page_1 = await http_server_client.fetch(
        service_base_url + "lectures?search=le&per_page=2&page=1", method="GET", headers=headers
    )
    assert page_1.code == HTTPStatus.OK
    data = json.loads(page_1.body.decode())
    assert data["page"] == 1
    assert data["per_page"] == 2
    assert data["total_items"] == 4
    assert data["total_pages"] == 2
    assert [lec["id"] for lec in data["lectures"]] == [1, 2]

    page_2 = await http_server_client.fetch(
        service_base_url + "lectures?search=le&per_page=2&page=2", method="GET", headers=headers
    )
    assert page_2.code == HTTPStatus.OK
    data = json.loads(page_2.body.decode())
    assert data["page"] == 2
    assert data["per_page"] == 2
    assert data["total_items"] == 4
    assert data["total_pages"] == 2
    assert [lec["id"] for lec in data["lectures"]] == [3, 41]

    # beyond the last page: empty but consistent metadata
    page_3 = await http_server_client.fetch(
        service_base_url + "lectures?search=le&per_page=2&page=3", method="GET", headers=headers
    )
    assert page_3.code == HTTPStatus.OK
    data = json.loads(page_3.body.decode())
    assert data["total_items"] == 4
    assert data["total_pages"] == 2
    assert data["lectures"] == []


async def test_get_lectures_search_with_complete_filter(
    app: GraderServer,
    service_base_url,
    http_server_client,
    default_token,
    default_roles,
    default_user_login,
    default_user,
    sql_alchemy_engine,
):
    # insert one complete and one active lecture matching the search term
    session: Session = sessionmaker(sql_alchemy_engine)()
    session.add(
        orm.Lecture(
            id=50,
            name="search_complete",
            code="c50",
            state=LectureState.complete,
            deleted=DeleteState.active,
        )
    )
    session.add(
        orm.Lecture(
            id=51,
            name="search_active",
            code="c51",
            state=LectureState.active,
            deleted=DeleteState.active,
        )
    )
    session.commit()

    add_role(sql_alchemy_engine, default_user.id, 50, Scope.instructor)
    add_role(sql_alchemy_engine, default_user.id, 51, Scope.instructor)

    headers = {"Authorization": f"Token {default_token}"}

    # without the complete filter both inserted lectures match
    response = await http_server_client.fetch(
        service_base_url + "lectures?search=search_", method="GET", headers=headers
    )
    assert response.code == HTTPStatus.OK
    data = json.loads(response.body.decode())
    assert [lec["id"] for lec in data["lectures"]] == [50, 51]
    assert data["total_items"] == 2

    # with complete=true only the complete lecture matches
    response = await http_server_client.fetch(
        service_base_url + "lectures?complete=true&search=search_", method="GET", headers=headers
    )
    assert response.code == HTTPStatus.OK
    data = json.loads(response.body.decode())
    assert [lec["id"] for lec in data["lectures"]] == [50]
    assert data["page"] == 1
    assert data["per_page"] == 20
    assert data["total_items"] == 1
    assert data["total_pages"] == 1
