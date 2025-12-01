# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
from http import HTTPStatus

import tornado
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import ObjectDeletedError
from tornado.web import HTTPError

from grader_service.api.models.lecture import Lecture as LectureModel
from grader_service.handlers.base_handler import GraderBaseHandler, authorize
from grader_service.orm.assignment import Assignment
from grader_service.orm.base import DeleteState
from grader_service.orm.lecture import Lecture, LectureState
from grader_service.orm.takepart import Role, Scope
from grader_service.registry import VersionSpecifier, register_handler


@register_handler(r"\/api\/lectures\/?", VersionSpecifier.ALL)
class LectureBaseHandler(GraderBaseHandler):
    """
    Tornado Handler class for http requests to /lectures.
    """

    @authorize([Scope.student, Scope.tutor, Scope.instructor, Scope.admin])
    async def get(self):
        """
        Returns all lectures the user can access.
        - For regular users: only lectures they have a role in, which match the requested state and are not deleted.
        - For admins: all lectures, regardless of state or deletion.
        """
        self.validate_parameters("complete")
        complete = self.get_argument("complete", "false") == "true"
        state = LectureState.complete if complete else LectureState.active

        if self.user.is_admin:
            lectures = self.session.query(Lecture).order_by(Lecture.id.asc()).all()
        else:
            lectures = sorted(
                [
                    role.lecture
                    for role in self.user.roles
                    if role.lecture.state == state and role.lecture.deleted == DeleteState.active
                ],
                key=lambda lecture: lecture.id,
            )

        self.write_json(lectures)

    @authorize([Scope.instructor, Scope.admin])
    async def post(self):
        """
        Creates a new lecture or updates an existing one.
        """
        self.validate_parameters()
        body = tornado.escape.json_decode(self.request.body)
        lecture_model = LectureModel.from_dict(body)

        lecture = (
            self.session.query(Lecture).filter(Lecture.code == lecture_model.code).one_or_none()
        )
        if lecture is None:
            lecture = Lecture()

        lecture.name = lecture_model.name
        lecture.code = lecture_model.code
        lecture.state = LectureState.complete if lecture_model.complete else LectureState.active
        lecture.deleted = DeleteState.active

        self.session.add(lecture)
        self.session.commit()
        self.set_status(HTTPStatus.CREATED)
        self.write_json(lecture)


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
        lecture_model = LectureModel.from_dict(body)
        lecture = self.session.get(Lecture, lecture_id)

        lecture.name = lecture_model.name
        lecture.state = LectureState.complete if lecture_model.complete else LectureState.active

        self.session.commit()
        self.write_json(lecture)

    @authorize([Scope.student, Scope.tutor, Scope.instructor, Scope.admin])
    async def get(self, lecture_id: int):
        """
        Finds lecture with the given lecture id.
        :param lecture_id: id of lecture
        :return: lecture with given id
        """
        self.validate_parameters()
        if self.user.is_admin:
            lecture = self.get_lecture(lecture_id)
            if lecture is None:
                raise HTTPError(HTTPStatus.NOT_FOUND, reason="Lecture was not found")
        else:
            role = self.get_role(lecture_id)
            lecture = role.lecture
            if lecture.deleted == DeleteState.deleted:
                raise HTTPError(HTTPStatus.NOT_FOUND, reason="Lecture was not found")
        self.write_json(lecture)

    @authorize([Scope.instructor, Scope.admin])
    async def delete(self, lecture_id: int):
        """
        Soft or Hard-Deletes a specific lecture.
        Soft deleting: lecture is still saved in the datastore
        but the users have no access to it.
        Hard deleting: removes lecture from the datastore and all associated directories/files.

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :raises HTTPError: throws err if lecture was already deleted
        or was not found

        """
        self.validate_parameters("hard_delete")
        hard_delete = self.get_argument("hard_delete", "false") == "true"

        try:
            lecture = self.get_lecture(lecture_id)
            if lecture is None:
                raise HTTPError(HTTPStatus.NOT_FOUND, reason="Lecture was not found")

            if hard_delete:
                if not self.user.is_admin:
                    raise HTTPError(HTTPStatus.FORBIDDEN, reason="Only Admins can hard-delete lecture.")

                self.delete_lecture_files(lecture)
                self.session.delete(lecture)
                self.session.commit()
            else:
                if lecture.deleted == DeleteState.deleted:
                    raise HTTPError(HTTPStatus.NOT_FOUND)

                lecture.deleted = DeleteState.deleted
                a: Assignment
                for a in lecture.assignments:
                    if len(a.submissions) > 0:
                        self.session.rollback()
                        raise HTTPError(
                            HTTPStatus.CONFLICT, "Cannot delete assignments with submissions!"
                        )
                    if a.status in ["released", "complete"]:
                        self.session.rollback()
                        raise HTTPError(
                            HTTPStatus.CONFLICT,
                            "Cannot delete released or completed assignments!",
                        )
                    a.deleted = DeleteState.deleted
                self.session.commit()
        except ObjectDeletedError:
            raise HTTPError(HTTPStatus.NOT_FOUND, reason="Lecture was not found")
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
        roles = (
            self.session.query(Role)
            .options(joinedload(Role.user))
            .filter(Role.lectid == lecture_id)
        )

        students = [r.user.id for r in roles if r.role == Scope.student]
        tutors = [r.user.id for r in roles if r.role == Scope.tutor]
        instructors = [r.user.id for r in roles if r.role == Scope.instructor]

        counts = {"instructors": instructors, "tutors": tutors, "students": students}
        self.write_json(counts)
