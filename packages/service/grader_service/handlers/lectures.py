# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
import re
from http import HTTPStatus

import tornado
from tornado.web import HTTPError

from grader_service.api.models import LectureUpdateDto, LectureCreateDto
from grader_service.handlers.base_handler import GraderBaseHandler, authorize
from grader_service.handlers.handler_utils import get_int_argument
from grader_service.orm.takepart import Scope
from grader_service.registry import VersionSpecifier, register_handler
from grader_service.services.lectures_service import (
    DEFAULT_PER_PAGE,
    MAX_PER_PAGE,
    LECTURE_SORTABLE_COLUMNS,
)

lecture_code_pattern = re.compile(r"^[A-Za-z0-9_-]+$")


@register_handler(r"\/api\/lectures\/?", VersionSpecifier.ALL)
class LectureBaseHandler(GraderBaseHandler):
    """
    Tornado Handler class for http requests to /lectures.
    """

    @authorize([Scope.student, Scope.tutor, Scope.instructor, Scope.admin])
    async def get(self):
        """
        Returns a paginated list of lectures the user can access.
        - For regular users: only lectures they have a role in, which match the requested states and are not deleted.
        - For admins: all lectures, regardless of the deletion state.

        Query parameters:
        - complete: filter by lecture state ("true" -> complete, otherwise active)
        - instructor: "true" -> only lectures where the user has an elevated role (if eligible)
        - page: 1-based page number (default 1)
        - per_page: items per page, 1-100 (default 20)
        - sort_by: "id" | "name" | "created_at" (default "id")
        - order: "asc" | "desc" (default "asc")
        - search: case-insensitive substring filter on lecture name and code
        """
        self.validate_parameters(
            "complete", "instructor", "page", "per_page", "sort_by", "order", "search"
        )
        complete = self.get_argument("complete", None)
        instructor = self.get_argument("instructor", None)
        search = self.get_argument("search", None)

        page = get_int_argument(self, "page", default=1, minimum=1)
        per_page = get_int_argument(
            self, "per_page", default=DEFAULT_PER_PAGE, minimum=1, maximum=MAX_PER_PAGE
        )

        sort_by = self.get_argument("sort_by", "created_at")
        if sort_by not in LECTURE_SORTABLE_COLUMNS:
            raise HTTPError(
                400, reason=f"Invalid sort_by: must be one of {sorted(LECTURE_SORTABLE_COLUMNS)}"
            )

        order = self.get_argument("order", "asc")
        if order not in ("asc", "desc"):
            raise HTTPError(400, reason="Invalid order: must be 'asc' or 'desc'")

        response = self.services.lectures.get_all_lectures(
            complete=complete,
            instructor_view=instructor,
            user=self.user,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            order=order,
            search=search,
        )
        self.write_json(response)

    @authorize([Scope.instructor, Scope.admin])
    async def post(self):
        """
        Creates a new lecture.
        :return: the created lecture
        :raises APIError: throws an error if the lecture code contains invalid characters or is already taken
        """
        self.validate_parameters()
        body = tornado.escape.json_decode(self.request.body)

        lecture = self.services.lectures.create_lecture(LectureCreateDto.from_dict(body))

        self.set_status(HTTPStatus.CREATED)
        self.write_json(lecture.dto_to_dict())


@register_handler(r"\/api\/lectures\/(?P<lecture_id>\d*)\/?", VersionSpecifier.ALL)
class LectureObjectHandler(GraderBaseHandler):
    """
    Tornado Handler class for http requests to /lectures/{lecture_id}.
    """

    @authorize([Scope.instructor, Scope.admin])
    async def put(self, lecture_id: int):
        """
        Updates a lecture.

        :param lecture_id: id of the lecture
        :type lecture_id: int
        """
        self.validate_parameters()
        body = tornado.escape.json_decode(self.request.body)
        lecture = self.services.lectures.update_lecture(
            lecture_id, LectureUpdateDto.from_dict(body), user=self.user
        )

        self.write_json(lecture.dto_to_dict())

    @authorize([Scope.student, Scope.tutor, Scope.instructor, Scope.admin])
    async def get(self, lecture_id: int):
        """
        Finds lecture with the given lecture id.
        :param lecture_id: id of the lecture
        :return: lecture with given id
        """
        self.validate_parameters()
        lecture = self.services.lectures.get_lecture_by_id(lecture_id, user=self.user)
        self.write_json(lecture.dto_to_dict())

    @authorize([Scope.instructor, Scope.admin])
    async def delete(self, lecture_id: int):
        """
        Soft or Hard-Deletes a specific lecture.
        Soft deleting: lecture is still saved in the datastore,
        but the users have no access to it.
        Hard deleting: removes lecture from the datastore and all associated directories/files.

        When performing a soft-delete of a lecture, all assignments in the lecture are also soft-deleted.
        If a previously soft-deleted assignment with the same name already exists in the lecture, that previous
        assignment is permanently removed (hard-deleted) before the current assignment is soft-deleted.

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :raises HTTPError: throws an error if the lecture was already deleted
        or was not found

        """
        self.validate_parameters("hard_delete")
        hard_delete = self.get_argument("hard_delete", "false") == "true"

        await self.services.lectures.delete_lecture(
            lecture_id, hard_delete=hard_delete, user=self.user
        )
        self.write("OK")


@register_handler(
    path=r"\/api\/lectures\/(?P<lecture_id>\d*)\/users\/?", version_specifier=VersionSpecifier.ALL
)
class LectureStudentsHandler(GraderBaseHandler):
    """
    Tornado Handler class for http requests to /lectures/{lecture_id}/users.
    """

    @authorize([Scope.tutor, Scope.instructor, Scope.admin])
    async def get(self, lecture_id: int):
        """
        Finds all users of a lecture and groups them by roles.

        :param lecture_id: id of the lecture
        :return: a dictionary of user, tutor and instructor names lists
        """
        students, tutors, instructors = self.services.lectures.get_lecture_users(lecture_id)

        lecture_users = {
            "instructors": [i.dto_to_dict() for i in instructors],
            "tutors": [t.dto_to_dict() for t in tutors],
            "students": [s.dto_to_dict() for s in students],
        }
        self.write_json(lecture_users)
