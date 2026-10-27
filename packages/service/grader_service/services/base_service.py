from http import HTTPStatus
from typing import Optional

from sqlalchemy import select, func

from grader_service.errors import APIError
from grader_service.orm import Role, User, Lecture, Assignment
from grader_service.orm.base import DeleteState
from grader_service.orm.takepart import Scope


class BaseService:
    def __init__(self, session_maker, file_service):
        self.session_maker = session_maker
        self.file_service = file_service

    def get_role(self, lecture_id: int, user: User, session) -> Role:
        role: Optional[Role] = session.get(Role, (user.id, lecture_id))
        if role is None:
            raise APIError(HTTPStatus.NOT_FOUND, "No role found")
        return role

    def has_elevated_permissions(self, session, user: User):
        stmt = select(
            select(Lecture)
            .join(Role)
            .where(
                Role.user_id == user.id,
                Role.role.in_([Scope.instructor, Scope.tutor]),
                Lecture.deleted == DeleteState.active,
            )
            .exists()
        )
        return session.execute(stmt).scalar()

    def get_assignment_counts(self, session, lecture_ids):
        stmt = (
            select(Assignment.lectid, func.count())
            .where(Assignment.lectid.in_(lecture_ids))
            .group_by(Assignment.lectid)
        )
        return dict(session.execute(stmt).all())

    def get_student_counts(self, session, lecture_ids):
        stmt = (
            select(Role.lectid, func.count())
            .where(Role.lectid.in_(lecture_ids), Role.role == Scope.student)
            .group_by(Role.lectid)
        )
        return dict(session.execute(stmt).all())

    def get_lecture(self, session, lecture_id: int) -> Lecture | None:
        lecture: Optional[Lecture] = session.get(Lecture, lecture_id)
        if lecture is None:
            raise APIError(HTTPStatus.NOT_FOUND, message="Lecture not found")
        return lecture

    def validate_assignment_for_soft_delete(self, assignment: Assignment):
        """Validates that an assignment can be soft-deleted.

        Raises an APIError if the assignment has submissions or is released/completed,
        preventing a soft-delete.

        :param assignment: the Assignment object to validate
        :type assignment: Assignment
        :raises APIError: if the assignment has submissions or is released/completed
        """
        if assignment.submissions:
            raise APIError(
                HTTPStatus.CONFLICT, message="Cannot delete assignments with submissions!"
            )
        if assignment.status in {"released", "complete"}:
            raise APIError(
                HTTPStatus.CONFLICT, message="Cannot delete released or completed assignments!"
            )

    def delete_previous_assignment(
        self, assignment: Assignment, lecture_id: int, session
    ) -> Optional[Assignment]:
        """Deletes a previously soft-deleted assignment with the same name in the lecture, if it exists.

        When performing a soft-delete, a previously soft-deleted assignment with the same
        name in the same lecture must be permanently removed (hard-deleted) first to avoid
        UNIQUE constraint violations before marking the current assignment as deleted.

        :param assignment: the Assignment object for which a previous duplicate may exist
        :type assignment: Assignment
        :param lecture_id: id of the lecture to which the assignment belongs
        :type lecture_id: int
        :return: the previously deleted Assignment if one existed, else None
        :rtype: Optional[Assignment]
        """
        stmt = select(Assignment).where(
            Assignment.lectid == lecture_id,
            Assignment.name == assignment.name,
            Assignment.deleted == DeleteState.deleted,
        )
        previously_deleted = session.execute(stmt).scalar_one_or_none()
        if previously_deleted is not None:
            session.delete(previously_deleted)
        return previously_deleted
