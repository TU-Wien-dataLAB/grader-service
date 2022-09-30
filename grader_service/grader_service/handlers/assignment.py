import json
import shutil
from http import HTTPStatus

import tornado
import os
from grader_convert.gradebook.models import GradeBookModel
from grader_service.api.models.assignment import Assignment as AssignmentModel
from grader_service.orm.assignment import Assignment, AutoGradingBehaviour
from grader_service.orm.base import DeleteState
from grader_service.orm.takepart import Role, Scope
from grader_service.registry import VersionSpecifier, register_handler
from sqlalchemy.exc import IntegrityError
from tornado.web import HTTPError
from .handler_utils import parse_ids

from grader_service.handlers.base_handler import GraderBaseHandler, authorize


@register_handler(
    path=r"\/lectures\/(?P<lecture_id>\d*)\/assignments\/?",
    version_specifier=VersionSpecifier.ALL,
)
class AssignmentBaseHandler(GraderBaseHandler):
    """
    Tornado Handler class for http requests to /lectures/{lecture_id}/assignments.
    """

    @authorize([Scope.student, Scope.tutor, Scope.instructor])
    async def get(self, lecture_id: int):
        """Returns all assignments of a lecture.

            :param lecture_id: id of the lecture
            :type lecture_id: int
            :raises HTTPError: throws err if lecture is deleted
            """
        lecture_id = parse_ids(lecture_id)
        self.validate_parameters()
        role = self.get_role(lecture_id)
        if role.lecture.deleted == DeleteState.deleted:
            raise HTTPError(HTTPStatus.NOT_FOUND, reason="Lecture not found")

        if (
                role.role == Scope.student
        ):  # students do not get assignments that are created
            assignments = (
                self.session.query(Assignment)
                .filter(
                    Assignment.lectid == role.lecture.id,
                    Assignment.deleted == DeleteState.active,
                    Assignment.status != "created",
                    Assignment.status != "pushed"
                )
                .all()
            )
        else:
            assignments = [
                a for a in role.lecture.assignments if a.deleted == DeleteState.active
            ]
        self.write_json(assignments)

    @authorize([Scope.instructor])
    async def post(self, lecture_id: int):
        """Creates a new assignment.

        :param lecture_id: id of the lecture
        :type lecture_id: int
        """
        lecture_id = parse_ids(lecture_id)
        self.validate_parameters()
        role = self.get_role(lecture_id)
        if role.lecture.deleted == DeleteState.deleted:
            raise HTTPError(HTTPStatus.NOT_FOUND)
        try:
            body = tornado.escape.json_decode(self.request.body)
            assignment_model = AssignmentModel.from_dict(body)
        except ValueError as e:
            # TODO Return useful error message
            raise HTTPError(HTTPStatus.BAD_REQUEST, log_message=str(e))
        assignment = Assignment()

        assignment.name = assignment_model.name
        assignment_with_name = self.session.query(Assignment) \
            .filter(Assignment.name == assignment.name, Assignment.deleted == DeleteState.active,
                    Assignment.lectid == lecture_id) \
            .one_or_none()

        if assignment_with_name is not None:
            raise HTTPError(HTTPStatus.CONFLICT, reason="Assignment name is already being used")
        if assignment_model.max_submissions is not None and assignment_model.max_submissions < 1:
            raise HTTPError(HTTPStatus.BAD_REQUEST, reason="Maximum number of submissions cannot be smaller than 1!")

        assignment.lectid = lecture_id
        assignment.duedate = assignment_model.due_date
        assignment.status = assignment_model.status
        assignment.type = assignment_model.type
        assignment.points = 0
        assignment.deleted = DeleteState.active
        assignment.automatic_grading = assignment_model.automatic_grading
        assignment.max_submissions = assignment_model.max_submissions
        assignment.allow_files = assignment_model.allow_files if assignment_model.allow_files is not None else False

        self.session.add(assignment)
        try:
            self.session.commit()
        except IntegrityError as e:
            self.log.error(e)
            self.session.rollback()
            raise HTTPError(HTTPStatus.UNPROCESSABLE_ENTITY, reason="Cannot add object to database.")
        self.set_status(HTTPStatus.CREATED)
        self.write_json(assignment)


@register_handler(
    path=r"\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/?",
    version_specifier=VersionSpecifier.ALL,
)
class AssignmentObjectHandler(GraderBaseHandler):
    """
    Tornado Handler class for http requests to /lectures/{lecture_id}/assignments/{assignment_id}.
    """

    @authorize([Scope.instructor])
    async def put(self, lecture_id: int, assignment_id: int):
        """Updates an assignment.

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        :raises HTTPError: throws err if assignment was not found
        """
        lecture_id, assignment_id = parse_ids(lecture_id, assignment_id)
        self.validate_parameters()
        body = tornado.escape.json_decode(self.request.body)
        assignment_model = AssignmentModel.from_dict(body)
        assignment = self.get_assignment(lecture_id, assignment_id)
        # Validate name
        assignment_with_name = self.session.query(Assignment) \
            .filter(Assignment.name == assignment_model.name, Assignment.deleted == DeleteState.active,
                    Assignment.lectid == assignment.lectid) \
            .one_or_none()

        if assignment_with_name is not None and assignment_with_name.id != assignment_id:
            raise HTTPError(HTTPStatus.CONFLICT, reason="Assignment name is already being used")
        if assignment_model.max_submissions is not None and assignment_model.max_submissions < 1:
            raise HTTPError(HTTPStatus.BAD_REQUEST, reason="Maximum number of submissions cannot be smaller than 1!")

        assignment.name = assignment_model.name
        assignment.duedate = assignment_model.due_date
        assignment.status = assignment_model.status
        assignment.type = assignment_model.type
        assignment.automatic_grading = assignment_model.automatic_grading
        assignment.max_submissions = assignment_model.max_submissions
        assignment.allow_files = assignment_model.allow_files if assignment_model.allow_files is not None else False

        if assignment.automatic_grading == AutoGradingBehaviour.full_auto.name and assignment.properties is not None:
            model = GradeBookModel.from_dict(json.loads(assignment.properties))
            _check_full_auto_grading(self, model)
        self.session.commit()
        self.write_json(assignment)

    @authorize([Scope.student, Scope.tutor, Scope.instructor])
    async def get(self, lecture_id: int, assignment_id: int):
        """Returns a specific assignment of a lecture.

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        :raises HTTPError: throws err if assignment was not found
        """
        lecture_id, assignment_id = parse_ids(lecture_id, assignment_id)
        self.validate_parameters("instructor-version")
        instructor_version = self.get_argument("instructor-version", "false") == "true"

        role = self.session.query(Role).get((self.user.name, lecture_id))
        if instructor_version and role.role < Scope.instructor:
            raise HTTPError(HTTPStatus.FORBIDDEN, reason="Forbidden")
        assignment = self.session.query(Assignment).get(assignment_id)
        if (
                assignment is None
                or assignment.deleted == DeleteState.deleted
                or (role.role == Scope.student and (assignment.status == "created" or assignment.status == "pushed"))
                or assignment.lectid != lecture_id
        ):
            raise HTTPError(HTTPStatus.NOT_FOUND, reason="Assignment was not found")
        self.write_json(assignment)

    @authorize([Scope.instructor])
    async def delete(self, lecture_id: int, assignment_id: int):
        """Soft-Deletes a specific assignment.

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        :raises HTTPError: throws err if assignment was not found or deleted
        """
        lecture_id, assignment_id = parse_ids(lecture_id, assignment_id)
        self.validate_parameters()
        assignment = self.get_assignment(lecture_id, assignment_id)

        if len(assignment.submissions) > 0:
            raise HTTPError(HTTPStatus.CONFLICT, reason="Can not delete assignment that has submissions")

        if assignment.status in ["released", "complete"]:
            raise HTTPError(HTTPStatus.CONFLICT,
                            reason=f'Cannot delete assignment with status "{assignment.status}"')

        previously_deleted = (
            self.session.query(Assignment)
            .filter(
                Assignment.lectid == lecture_id,
                Assignment.name == assignment.name,
                Assignment.deleted == DeleteState.deleted,
            )
            .one_or_none()
        )
        if previously_deleted is not None:
            self.session.delete(previously_deleted)
            self.session.commit()

        assignment.deleted = DeleteState.deleted
        self.session.commit()


@register_handler(
    path=r"\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/reset\/?",
    version_specifier=VersionSpecifier.ALL,
)
class AssignmentResetHandler(GraderBaseHandler):
    """
    Tornado Handler class for http requests to /lectures/{lecture_id}/assignments/{assignment_id}/reset.
    """

    @authorize([Scope.instructor, Scope.tutor, Scope.student])
    async def get(self, lecture_id: int, assignment_id: int):
        self.validate_parameters()
        lecture_id, assignment_id = parse_ids(lecture_id, assignment_id)
        assignment = self.get_assignment(lecture_id, assignment_id)

        git_path_base = os.path.join(self.application.grader_service_dir, "tmp", assignment.lecture.code,
                                     assignment.name, self.user.name)
        # Deleting dir
        if os.path.exists(git_path_base):
            shutil.rmtree(git_path_base)

        self.log.info(f"DIR {git_path_base}")
        os.makedirs(git_path_base, exist_ok=True)
        git_path_release = os.path.join(git_path_base, "release")
        git_path_user = os.path.join(git_path_base, self.user.name)
        self.log.info(f"GIT BASE {git_path_base}")
        self.log.info(f"GIT RELEASE {git_path_release}")
        self.log.info(f"GIT USER {git_path_user}")

        repo_path_release = self.construct_git_dir('release', assignment.lecture, assignment)
        repo_path_user = self.construct_git_dir(assignment.type, assignment.lecture, assignment)

        self.duplicate_release_repo(repo_path_release=repo_path_release,
                                    repo_path_user=repo_path_user,
                                    assignment=assignment,
                                    message="Reset Assignment")

        self.write_json(assignment)


@register_handler(
    path=r"\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/properties\/?",
    version_specifier=VersionSpecifier.ALL,
)
class AssignmentPropertiesHandler(GraderBaseHandler):
    """
    Tornado Handler class for http requests to /lectures/{lecture_id}/assignments/{assignment_id}/properties.
    """

    @authorize([Scope.tutor, Scope.instructor])
    async def get(self, lecture_id: int, assignment_id: int):
        """
        Returns the properties of a specific assignment.

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        :raises HTTPError: throws err if the assignment or their properties were not found
        """
        lecture_id, assignment_id = parse_ids(lecture_id, assignment_id)
        self.validate_parameters()
        assignment = self.get_assignment(lecture_id, assignment_id)
        if assignment.properties is not None:
            self.write(assignment.properties)
        else:
            raise HTTPError(HTTPStatus.NOT_FOUND, reason="Assignment not found")

    @authorize([Scope.tutor, Scope.instructor])
    async def put(self, lecture_id: int, assignment_id: int):
        """
        Updates the properties of a specific assignment.

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        :raises HTTPError: throws err if the assignment was not found
        """
        lecture_id, assignment_id = parse_ids(lecture_id, assignment_id)
        self.validate_parameters()
        assignment = self.get_assignment(lecture_id, assignment_id)
        properties_string: str = self.request.body.decode("utf-8")

        model = GradeBookModel.from_dict(json.loads(properties_string))
        # Check if assignment contains no cells that need manual grading if assignment is fully auto graded
        if assignment.automatic_grading == AutoGradingBehaviour.full_auto:
            _check_full_auto_grading(self, model)

        assignment.properties = properties_string
        assignment.points = model.max_score
        self.session.commit()


def _check_full_auto_grading(self: GraderBaseHandler, model):
    """
    Checks if the assignment notebook contain manual graded cells and throws an error if they do.

    :param self: handler class
    :param model: the notebook which is being tested
    :return: void
    """
    for nb in model.notebooks.values():
        if len(nb.task_cells_dict) > 0:
            raise HTTPError(HTTPStatus.CONFLICT, reason="Fully autograded notebook cannot contain task cells!")
        grades = set(nb.grade_cells_dict.keys())
        solutions = set(nb.solution_cells_dict.keys())
        if len(grades & solutions) > 0:
            raise HTTPError(HTTPStatus.CONFLICT,
                            reason="Fully autograded notebook cannot contain manually graded cells!")
