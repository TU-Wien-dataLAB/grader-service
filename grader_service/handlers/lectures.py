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

    @authorize([Scope.student, Scope.tutor, Scope.instructor])
    async def get(self):
        """
        Returns all lectures the user can access.
        """
        self.validate_parameters("complete")
        complete = self.get_argument("complete", None)
        if complete is None:  # return both complete and active lectures
            lectures = sorted(
                [
                    role.lecture
                    for role in self.user.roles
                    if role.lecture.deleted == DeleteState.active
                ],
                key=lambda lecture: lecture.id,
            )
        else:  # return either only complete or only active lectures
            state = LectureState.complete if (complete == "true") else LectureState.active
            lectures = sorted(
                [
                    role.lecture
                    for role in self.user.roles
                    if role.lecture.state == state and role.lecture.deleted == DeleteState.active
                ],
                key=lambda lecture: lecture.id,
            )

        self.write_json(lectures)

    @authorize([Scope.instructor])
    async def post(self):
        """
        Creates a new lecture from a "ghost"-lecture.

        :raises HTTPError: throws err if "ghost"-lecture was not found
        """
        self.validate_parameters()
        body = tornado.escape.json_decode(self.request.body)
        lecture_model = LectureModel.from_dict(body)

        lecture = (
            self.session.query(Lecture).filter(Lecture.code == lecture_model.code).one_or_none()
        )
        if lecture is None:
            raise HTTPError(HTTPStatus.NOT_FOUND, reason="Lecture template not found")

        lecture.name = lecture_model.name
        lecture.code = lecture_model.code
        lecture.state = LectureState.complete if lecture_model.complete else LectureState.active
        lecture.deleted = DeleteState.active

        self.session.commit()
        self.set_status(HTTPStatus.CREATED)
        self.write_json(lecture)


@register_handler(r"\/api\/lectures\/(?P<lecture_id>\d*)\/?", VersionSpecifier.ALL)
class LectureObjectHandler(GraderBaseHandler):
    """
    Tornado Handler class for http requests to /lectures/{lecture_id}.
    """

    @authorize([Scope.instructor])
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

    @authorize([Scope.student, Scope.tutor, Scope.instructor])
    async def get(self, lecture_id: int):
        """
        Finds lecture with the given lecture id.
        :param lecture_id: id of lecture
        :return: lecture with given id
        """
        self.validate_parameters()
        role = self.get_role(lecture_id)
        if role.lecture.deleted == DeleteState.deleted:
            raise HTTPError(HTTPStatus.NOT_FOUND, reason="Lecture was not found")

        self.write_json(role.lecture)

    @authorize([Scope.instructor])
    async def delete(self, lecture_id: int):
        """
        "Soft"-delete a lecture.
        Softdeleting: lecture is still saved in the datastore
        but the users have not access to it.

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :raises HTTPError: throws err if lecture was already deleted
        or was not found

        """
        self.validate_parameters()
        try:
            lecture = self.session.get(Lecture, lecture_id)
            if lecture.deleted == 1:
                raise HTTPError(404)
            lecture.deleted = 1
            a: Assignment
            for a in lecture.assignments:
                if (len(a.submissions)) > 0:
                    self.session.rollback()
                    raise HTTPError(
                        HTTPStatus.CONFLICT, "Cannot delete assignment because it has submissions"
                    )
                if a.status in ["released", "complete"]:
                    self.session.rollback()
                    raise HTTPError(
                        HTTPStatus.CONFLICT,
                        "Cannot delete assignment because its status is not created",
                    )

                a.deleted = 1
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

    @authorize([Scope.tutor, Scope.instructor])
    async def get(self, lecture_id: int):
        """
        Finds all users of a lecture and groups them by roles.

        :param lecture_id: id of the lecture
        :return: a dictionary of user, tutor and instructor names lists
        """
        students = (
            self.session.query(Role)
            .options(joinedload(Role.user))
            .filter(Role.lectid == lecture_id)
            .filter(Role.role == Scope.student)
        )
        tutors = (
            self.session.query(Role)
            .options(joinedload(Role.user))
            .filter(Role.lectid == lecture_id)
            .filter(Role.role == Scope.tutor)
        )
        instructors = (
            self.session.query(Role)
            .options(joinedload(Role.user))
            .filter(Role.lectid == lecture_id)
            .filter(Role.role == Scope.instructor)
        )

        students = [
            {"id": s.user.id, "name": s.user.name, "display_name": s.user.display_name}
            for s in students
        ]
        tutors = [
            {"id": t.user.id, "name": t.user.name, "display_name": t.user.display_name}
            for t in tutors
        ]
        instructors = [
            {"id": i.user.id, "name": i.user.name, "display_name": i.user.display_name}
            for i in instructors
        ]

        counts = {"instructors": instructors, "tutors": tutors, "students": students}
        self.write_json(counts)
