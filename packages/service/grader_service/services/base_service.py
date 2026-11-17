from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from grader_service.errors import NotFoundError, ConflictError
from grader_service.orm import Role, User, Lecture, Assignment, Submission
from grader_service.orm.base import DeleteState
from grader_service.orm.takepart import Scope
from grader_service.services.file_services.base_file_service import FileService


class BaseService:
    """Base class for services.

    Services contain all database and business logic. They do not manage a session lifecycle.
    """

    def __init__(self, file_service: FileService):
        self.file_service = file_service

    def get_role(self, session: Session, lecture_id: int, user: User) -> Role:
        role: Optional[Role] = session.get(Role, (user.id, lecture_id))
        if role is None:
            raise NotFoundError("No role found")
        return role

    def has_elevated_permissions(self, session: Session, user: User) -> bool | None:
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

    def get_assignment_counts(self, session: Session, lecture_ids: list[int]) -> dict:
        stmt = (
            select(Assignment.lectid, func.count())
            .where(Assignment.lectid.in_(lecture_ids))
            .group_by(Assignment.lectid)
        )
        return dict(session.execute(stmt).all())

    def get_student_counts(self, session: Session, lecture_ids) -> dict:
        stmt = (
            select(Role.lectid, func.count())
            .where(Role.lectid.in_(lecture_ids), Role.role == Scope.student)
            .group_by(Role.lectid)
        )
        return dict(session.execute(stmt).all())

    def get_lecture(self, session: Session, lecture_id: int) -> Lecture | None:
        lecture: Optional[Lecture] = session.get(Lecture, lecture_id)
        if lecture is None:
            raise NotFoundError("Lecture not found")
        return lecture

    def validate_assignments_for_soft_delete(
        self, session: Session, assignments: list[Assignment]
    ) -> None:
        """Validates that all assignments can be soft-deleted.

        Raises a ServiceError if any assignment has submissions or is released/completed,
        preventing a soft-delete. Submission counts are fetched in a single grouped
        query instead of one lazy load per assignment.

        :param session: the database session
        :param assignments: the Assignment objects to validate
        :raises ConflictError: if an assignment has submissions or is released/completed
        """
        assignment_ids = [a.id for a in assignments]
        submission_counts = {}
        if assignment_ids:
            submission_counts = dict(
                session.execute(
                    select(Submission.assignid, func.count())
                    .where(Submission.assignid.in_(assignment_ids))
                    .group_by(Submission.assignid)
                ).all()
            )
        for assignment in assignments:
            if submission_counts.get(assignment.id, 0) > 0:
                raise ConflictError("Cannot delete assignments with submissions!")
            if assignment.status in {"released", "complete"}:
                raise ConflictError("Cannot delete released or completed assignments!")

    def delete_previous_assignments(
        self, session: Session, assignments: list[Assignment], lecture_id: int
    ) -> list[int]:
        """Deletes previously soft-deleted assignments with the same names, if they exist.

        When performing a soft-delete, previously soft-deleted assignments with the same
        names in the same lecture must be permanently removed (hard-deleted) first to avoid
        UNIQUE constraint violations before marking the current assignments as deleted.
        All duplicates are fetched with a single query instead of one per assignment.

        :param assignments: the Assignment objects for which previous duplicates may exist
        :param lecture_id: id of the lecture to which the assignments belong
        :param session: the database session
        :return: the ids of the previously deleted assignments
        """
        names = [a.name for a in assignments]
        if not names:
            return []
        previously_deleted = session.scalars(
            select(Assignment).where(
                Assignment.lectid == lecture_id,
                Assignment.name.in_(names),
                Assignment.deleted == DeleteState.deleted,
            )
        ).all()
        # capture the ids before the objects are deleted from the session
        previously_deleted_ids = [a.id for a in previously_deleted]
        for assignment in previously_deleted:
            session.delete(assignment)
        return previously_deleted_ids
