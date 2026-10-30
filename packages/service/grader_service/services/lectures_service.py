import logging
import math
import re
from http import HTTPStatus

from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from grader_service.api.models import (
    LectureDetailDto,
    LectureUpdateDto,
    LectureCreateDto,
    LectureListDto,
)
from grader_service.api.models.user import User as UserDto
from grader_service.errors import APIError
from grader_service.orm.base import DeleteState
from grader_service.orm.lecture import LectureState
from grader_service.orm.takepart import Scope
from grader_service.services.base_service import BaseService
from grader_service.orm import User, Lecture, Role
from grader_service.services.mappers.lectures_mapper import (
    to_lecture_list_item_dto,
    to_lecture_detail_dto,
)
from grader_service.services.mappers.users_mapper import to_user_dto

log = logging.getLogger(__name__)

lecture_code_pattern = re.compile(r"^[A-Za-z0-9_-]+$")

# Allow-list of sortable lecture columns
LECTURE_SORTABLE_COLUMNS = {
    "id": Lecture.id,
    "name": Lecture.name,
    "created_at": Lecture.created_at,
}

DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 100


class LecturesService(BaseService):
    def get_all_lectures(
        self,
        complete: bool | None,
        instructor_view: bool | None,
        user: User,
        page: int = 1,
        per_page: int = DEFAULT_PER_PAGE,
        sort_by: str = "created_at",
        order: str = "asc",
        search: str | None = None,
    ) -> LectureListDto:
        with self.session_maker() as session:
            stmt = select(Lecture)
            if not user.is_admin:
                stmt = stmt.join(Role).where(
                    Role.user_id == user.id, Lecture.deleted == DeleteState.active
                )

                if instructor_view and self.has_elevated_permissions(session, user):
                    stmt = stmt.where(Role.role.in_([Scope.instructor, Scope.tutor]))

            total_items_unfiltered = session.execute(
                select(func.count()).select_from(stmt.subquery())
            ).scalar_one()

            if complete is not None:
                state = LectureState.complete if complete else LectureState.active
                stmt = stmt.where(Lecture.state == state)

            if search:
                # escape LIKE wildcards so user input matches literally
                escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
                term = f"%{escaped}%"
                stmt = stmt.where(
                    Lecture.name.ilike(term, escape="\\") | Lecture.code.ilike(term, escape="\\")
                )

            # total count under the same filters the user can see,
            # so pagination metadata is consistent with the page contents
            total_items = session.execute(
                select(func.count()).select_from(stmt.subquery())
            ).scalar_one()

            sort_column = LECTURE_SORTABLE_COLUMNS[sort_by]
            is_ascending = order == "asc"
            ordering = [sort_column.asc() if is_ascending else sort_column.desc()]
            if sort_by != "id":
                # deterministic tiebreaker so pages are stable when sort values repeat
                ordering.append(Lecture.id.asc() if is_ascending else Lecture.id.desc())

            stmt = stmt.order_by(*ordering).offset((page - 1) * per_page).limit(per_page)
            lectures = session.scalars(stmt).all()
            ids = [lec.id for lec in lectures]
            a_counts = self.get_assignment_counts(session, ids)
            s_counts = self.get_student_counts(session, ids)

            lecture_dtos = [
                to_lecture_list_item_dto(
                    lec,
                    a_counts.get(lec.id, 0),
                    s_counts.get(lec.id, 0) if instructor_view else None,
                )
                for lec in lectures
            ]

            total_pages = math.ceil(total_items / per_page) if total_items > 0 else 0
            return LectureListDto(
                lectures=[lec.dto_to_dict(omit_if_none={"student_count"}) for lec in lecture_dtos],
                page=page,
                per_page=per_page,
                total_items=total_items,
                total_pages=total_pages,
                total_items_unfiltered=total_items_unfiltered,
            )

    def get_lecture_by_id(self, lecture_id: int, user: User) -> LectureDetailDto:
        with self.session_maker() as session:
            lecture = self.get_lecture(session, lecture_id)

            if not user.is_admin:
                if lecture.deleted == DeleteState.deleted:
                    raise APIError(HTTPStatus.NOT_FOUND, message="Lecture not found")
            return to_lecture_detail_dto(lecture)

    def create_lecture(self, lecture_dto: LectureCreateDto) -> LectureDetailDto:
        with self.session_maker() as session:
            try:
                if not lecture_code_pattern.fullmatch(lecture_dto.code or ""):
                    raise APIError(
                        HTTPStatus.BAD_REQUEST,
                        message="Invalid lecture code: only alphanumeric characters, '-' and '_' are allowed.",
                    )
                lecture = session.scalars(
                    select(Lecture).where(Lecture.code == lecture_dto.code)
                ).first()
                if lecture is not None:
                    raise APIError(HTTPStatus.CONFLICT, message="Lecture code already in use")

                lecture = Lecture()
                lecture.name = lecture_dto.name
                lecture.code = lecture_dto.code
                lecture.state = (
                    LectureState.complete if lecture_dto.complete else LectureState.active
                )
                lecture.deleted = DeleteState.active

                session.add(lecture)
                session.commit()
            except IntegrityError:
                # the unique constraint on the code caught a concurrent create
                session.rollback()
                raise APIError(HTTPStatus.CONFLICT, message="Lecture code already in use")
            except Exception:
                if session.in_transaction():
                    session.rollback()
                raise

            return to_lecture_detail_dto(lecture)

    def update_lecture(self, lecture_id: int, lecture_dto: LectureUpdateDto, user: User):
        with self.session_maker() as session:
            try:
                lecture = self.get_lecture(session, lecture_id)
                if not user.is_admin and lecture.deleted == DeleteState.deleted:
                    raise APIError(HTTPStatus.NOT_FOUND, message="Lecture was deleted.")

                lecture.name = lecture_dto.name
                lecture.state = (
                    LectureState.complete if lecture_dto.complete else LectureState.active
                )

                session.commit()
                return to_lecture_detail_dto(lecture)
            except Exception:
                if session.in_transaction():
                    session.rollback()
                raise

    async def delete_lecture(self, lecture_id: int, hard_delete: bool, user: User) -> None:
        with self.session_maker() as session:
            try:
                lecture = self.get_lecture(session, lecture_id)
                # capture the code before any commit, since accessing attributes of
                # ORM objects after they were deleted from the session is fragile
                lecture_code = lecture.code
                if hard_delete:
                    if not user.is_admin:
                        raise APIError(
                            HTTPStatus.FORBIDDEN, message="Only Admins can hard-delete lecture."
                        )

                    session.delete(lecture)
                    session.commit()
                    try:
                        await self.file_service.delete_lecture_files(lecture_code)
                    except Exception:
                        # the lecture is already deleted from the database; a file system
                        # error must not turn the successful delete into a server error
                        log.exception("Failed to delete files of lecture %s", lecture_code)
                else:
                    if lecture.deleted == DeleteState.deleted:
                        raise APIError(HTTPStatus.NOT_FOUND, message="Lecture was deleted.")

                    assignments = list(lecture.assignments)
                    self.validate_assignments_for_soft_delete(session, assignments)
                    previously_deleted_assignments = self.delete_previous_assignments(
                        assignments=assignments, lecture_id=lecture_id, session=session
                    )

                    # Flush so the duplicate DELETEs are executed before the UPDATEs
                    # that mark the current assignments as deleted.
                    session.flush()

                    for assignment in assignments:
                        assignment.deleted = DeleteState.deleted

                    lecture.deleted = DeleteState.deleted
                    session.commit()

                    # the lecture and its assignments are now soft-deleted; the files of
                    # the removed duplicates are cleaned up best-effort below
                    for assignment_id in previously_deleted_assignments:
                        try:
                            await self.file_service.delete_assignment_files(
                                assignment_id, lecture_code
                            )
                        except Exception:
                            # the deletes are already committed; log leftover files
                            # so they can be cleaned up manually
                            log.exception(
                                "Failed to delete files of assignment %s in lecture %s",
                                assignment_id,
                                lecture_code,
                            )
            except Exception:
                if session.in_transaction():
                    session.rollback()
                raise

    def get_lecture_users(
        self, lecture_id: int
    ) -> tuple[list[UserDto], list[UserDto], list[UserDto]]:
        with self.session_maker() as session:
            roles = session.scalars(
                select(Role).options(joinedload(Role.user)).where(Role.lectid == lecture_id)
            ).all()
            students, tutors, instructors = [], [], []
            for role in roles:
                if role.role == Scope.student:
                    students.append(to_user_dto(role.user))
                elif role.role == Scope.tutor:
                    tutors.append(to_user_dto(role.user))
                elif role.role == Scope.instructor:
                    instructors.append(to_user_dto(role.user))
            return students, tutors, instructors
