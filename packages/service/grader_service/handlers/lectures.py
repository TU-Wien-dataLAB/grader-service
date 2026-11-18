# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
from http import HTTPStatus


from grader_service.api.models import LectureUpdateDto, LectureCreateDto
from grader_service.errors import ServiceError, APIError
from grader_service.handlers.base_handler import GraderBaseHandler, authorize
from grader_service.orm.takepart import Scope
from grader_service.registry import VersionSpecifier, register_handler
from grader_service.services.lectures_service import (
    LECTURE_SORTABLE_COLUMNS,
    DEFAULT_PER_PAGE,
    MAX_PER_PAGE,
)


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
        - complete: "true" | "false" -> filter by lecture state (complete or active)
        - instructor: "true" -> only lectures where the user has an elevated role (if eligible)
        - page: 1-based page number (default 1)
        - per_page: items per page, 1-100 (DEFAULT_PER_PAGE = 20, MAX_PER_PAGE = 100)
        - sort_by: "id" | "name" | "created_at" (default "created_at")
        - order: "asc" | "desc" (default "asc")
        - search: case-insensitive substring filter on lecture name and code
        """
        self.validate_parameters(
            "complete", "instructor", "page", "per_page", "sort_by", "order", "search"
        )
        complete = self.get_bool_argument("complete")
        instructor = self.get_bool_argument("instructor")
        # only hit the database for the permission check if the instructor view was requested
        has_elevated_permissions = instructor and self.services.lectures.has_elevated_permissions(
            self.session, self.user
        )
        search = self.get_argument("search", None)

        page = self.get_int_argument("page", default=1, minimum=1)
        per_page = self.get_int_argument(
            "per_page", default=DEFAULT_PER_PAGE, minimum=1, maximum=MAX_PER_PAGE
        )

        sort_by = self.get_argument("sort_by", "created_at")
        if sort_by not in LECTURE_SORTABLE_COLUMNS:
            raise APIError(
                400, message=f"Invalid sort_by: must be one of {sorted(LECTURE_SORTABLE_COLUMNS)}"
            )

        order = self.get_argument("order", "asc")
        if order not in ("asc", "desc"):
            raise APIError(400, message="Invalid order: must be 'asc' or 'desc'")

        lectures = self.services.lectures.get_all_lectures(
            self.session,
            complete=complete,
            has_elevated_permissions=has_elevated_permissions,
            user=self.user,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            order=order,
            search=search,
        )
        self.write_json(lectures)

    @authorize([Scope.instructor, Scope.admin])
    async def post(self):
        """
        Creates a new lecture.
        :return: the created lecture
        :raises APIError: throws an error if the lecture code contains invalid characters or is already taken
        """
        self.validate_parameters()
        try:
            lecture = self.services.lectures.create_lecture(
                self.session, self.parse_json_dto(LectureCreateDto)
            )
        except ServiceError as e:
            raise self.to_api_error(e)

        self.set_status(HTTPStatus.CREATED)
        self.write_json(lecture)


@register_handler(r"\/api\/lectures\/(?P<lecture_id>\d*)\/?", VersionSpecifier.ALL)
class LectureObjectHandler(GraderBaseHandler):
    """
    Tornado Handler class for http requests to /lectures/{lecture_id}.
    """

    @authorize([Scope.student, Scope.tutor, Scope.instructor, Scope.admin])
    async def get(self, lecture_id: int):
        """
        Finds lecture with the given lecture id.
        :param lecture_id: id of the lecture
        :return: lecture with given id
        """
        self.validate_parameters()
        try:
            lecture = self.services.lectures.get_lecture_by_id(
                self.session, lecture_id, can_get_deleted_lecture=self.user.is_admin
            )
        except ServiceError as e:
            raise self.to_api_error(e)
        self.write_json(lecture)

    @authorize([Scope.instructor, Scope.admin])
    async def put(self, lecture_id: int):
        """
        Updates a lecture.

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :return: updated lecture
        """
        self.validate_parameters()
        try:
            lecture = self.services.lectures.update_lecture(
                self.session,
                lecture_id,
                self.parse_json_dto(LectureUpdateDto),
                can_update_deleted_lecture=self.user.is_admin,
            )
        except ServiceError as e:
            raise self.to_api_error(e)

        self.write_json(lecture)

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
        :raises APIError: throws an error if the lecture was already deleted, was not found, or
        a user is not authorized to hard delete the lecture

        """
        self.validate_parameters("hard_delete")
        hard_delete = self.get_bool_argument("hard_delete", default=False)

        try:
            if hard_delete:
                if not self.user.is_admin:
                    raise APIError(
                        HTTPStatus.FORBIDDEN, message="Only admins can hard-delete lectures."
                    )
                await self.services.lectures.hard_delete_lecture(self.session, lecture_id)
            else:
                await self.services.lectures.soft_delete_lecture(self.session, lecture_id)
        except ServiceError as e:
            raise self.to_api_error(e)
        self.set_status(HTTPStatus.NO_CONTENT)


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
        students, tutors, instructors = self.services.lectures.get_lecture_users(
            self.session, lecture_id
        )

        lecture_users = {"instructors": instructors, "tutors": tutors, "students": students}
        self.write_json(lecture_users)
