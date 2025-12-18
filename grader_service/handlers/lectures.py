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
        complete = self.get_argument("complete", None)

        query = self.session.query(Lecture)

        if complete is not None:
            state = LectureState.complete if complete == "true" else LectureState.active
            query = query.filter(Lecture.state == state)

        if not self.user.is_admin:
            query = query.join(Role).filter(
                Role.user_id == self.user.id, Lecture.deleted == DeleteState.active
            )

        lectures = query.order_by(Lecture.id.asc()).all()
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

        When performing a soft-delete of a lecture, all assignments in the lecture are also soft-deleted.
        If a previously soft-deleted assignment with the same name already exists in the lecture, that previous
        assignment is permanently removed (hard-deleted) before the current assignment is soft-deleted.

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
                    raise HTTPError(
                        HTTPStatus.FORBIDDEN, reason="Only Admins can hard-delete lecture."
                    )

                self.session.delete(lecture)
                self.session.commit()
                self.delete_lecture_files(lecture)
            else:
                if lecture.deleted == DeleteState.deleted:
                    raise HTTPError(HTTPStatus.NOT_FOUND)

                # Collect previous duplicates and delete them before commit
                # to prevent UNIQUE constraint violations when soft-deleting current assignments
                previously_deleted_assignments = []
                for assignment in lecture.assignments:
                    self.validate_assignment_for_soft_delete(assignment=assignment)
                    previously_deleted = self.delete_previous_assignment(
                        assignment=assignment, lecture_id=lecture_id
                    )
                    if previously_deleted is not None:
                        previously_deleted_assignments.append(previously_deleted)
                self.session.commit()

                for assignment in previously_deleted_assignments:
                    self.delete_assignment_files(assignment=assignment, lecture=lecture)

                for assignment in lecture.assignments:
                    assignment.deleted = DeleteState.deleted

                lecture.deleted = DeleteState.deleted
                self.session.commit()

            self.write("OK")
        except ObjectDeletedError:
            self.session.rollback()
            raise HTTPError(HTTPStatus.NOT_FOUND, reason="Assignment was not found")
        except Exception:
            self.session.rollback()
            raise


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
