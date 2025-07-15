import datetime
import json
import os
import shutil
from http import HTTPStatus
from pathlib import Path
from typing import Union

import isodate
import tornado
from sqlalchemy.exc import IntegrityError
from tornado.web import HTTPError

from grader_service.api.models.assignment import Assignment as AssignmentModel
from grader_service.api.models.assignment_settings import AssignmentSettings
from grader_service.convert.gradebook.models import GradeBookModel
from grader_service.handlers.base_handler import GraderBaseHandler, authorize
from grader_service.handlers.submissions import SubmissionHandler
from grader_service.orm.assignment import Assignment
from grader_service.orm.base import DeleteState
from grader_service.orm.submission import Submission
from grader_service.orm.takepart import Role, Scope
from grader_service.registry import VersionSpecifier, register_handler

from .handler_utils import GitRepoType, parse_ids


def validate_assignment_settings(settings: Union[AssignmentSettings, None]):
    if settings is None:
        return
    late_submission = settings.late_submission or []
    current_period = isodate.parse_duration("P0D")
    curr_scaling = 1.0
    for period in late_submission:
        try:
            d = isodate.parse_duration(period.period)
            if d < datetime.timedelta(0):
                raise ValueError
            if not isinstance(period.scaling, float):
                raise TypeError
            s = period.scaling
        except (isodate.isoerror.ISO8601Error, TypeError, ValueError):
            raise HTTPError(HTTPStatus.BAD_REQUEST, reason="Invalid settings!")
        if d <= current_period:
            raise HTTPError(HTTPStatus.BAD_REQUEST, reason="Period lengths are not increasing!)")
        if s <= 0.0 or s >= 1.0:
            raise HTTPError(
                HTTPStatus.BAD_REQUEST,
                reason="Score scaling has to be between 0.0 and 1.0 exclusive!",
            )
        if s >= curr_scaling:
            raise HTTPError(HTTPStatus.BAD_REQUEST, reason="Score scaling is not decreasing!")
        current_period = d
        curr_scaling = s


@register_handler(
    path=r"\/api\/lectures\/(?P<lecture_id>\d*)\/assignments\/?",
    version_specifier=VersionSpecifier.ALL,
)
class AssignmentBaseHandler(GraderBaseHandler):
    """Tornado Handler for http requests

    route: /lectures/{lecture_id}/assignments."""

    @authorize([Scope.student, Scope.tutor, Scope.instructor])
    async def get(self, lecture_id: int):
        """Returns all assignments of a lecture.

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :raises HTTPError: throws err if lecture is deleted
        """
        lecture_id = parse_ids(lecture_id)
        self.validate_parameters("include-submissions")
        role = self.get_role(lecture_id)
        if role.lecture.deleted == DeleteState.deleted:
            raise HTTPError(HTTPStatus.NOT_FOUND, reason="Lecture not found")

        if role.role == Scope.student:  # students do not get assignments that are created
            assignments = (
                self.session.query(Assignment)
                .filter(
                    Assignment.lectid == role.lecture.id,
                    Assignment.deleted == DeleteState.active,
                    Assignment.status != "created",
                    Assignment.status != "pushed",
                )
                .all()
            )

        else:
            assignments = [a for a in role.lecture.assignments if (a.deleted == DeleteState.active)]

        # Handle the case that the user wants to include submissions
        include_submissions = self.get_argument("include-submissions", "true") == "true"
        if include_submissions:
            assignids = [a.id for a in assignments]
            username = self.user.name
            results = (
                self.session.query(Submission)
                .filter(Submission.assignid.in_(assignids), Submission.username == username)
                .all()
            )
            # Create a combined list of assignments and submissions
            assignments = [a.serialize() for a in assignments]
            submissions = [s.serialize() for s in results]
            for a in assignments:
                a["submissions"] = [s for s in submissions if s["assignid"] == a["id"]]
        assignments = sorted(assignments, key=lambda o: o["id"])
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
            raise HTTPError(HTTPStatus.BAD_REQUEST, reason=str(e))
        assignment = Assignment()

        assignment.name = assignment_model.name
        assignment_with_name = (
            self.session.query(Assignment)
            .filter(
                Assignment.name == assignment.name,
                Assignment.deleted == DeleteState.active,
                Assignment.lectid == lecture_id,
            )
            .one_or_none()
        )

        if assignment_with_name is not None:
            raise HTTPError(HTTPStatus.CONFLICT, reason="Assignment name is already being used")
        if assignment_model.settings is None:
            raise HTTPError(HTTPStatus.BAD_REQUEST, reason="Assignment missing settings key")
        if (assignment_model.settings.max_submissions is not None) and (
            assignment_model.settings.max_submissions < 1
        ):
            msg = "Maximum number of submissions cannot be smaller than 1!"
            raise HTTPError(HTTPStatus.BAD_REQUEST, reason=msg)
        validate_assignment_settings(assignment_model.settings)

        assignment.lectid = lecture_id
        assignment.status = assignment_model.status
        assignment.points = 0
        assignment.deleted = DeleteState.active
        assignment.settings = assignment_model.settings

        self.session.add(assignment)
        try:
            self.session.commit()
        except IntegrityError as e:
            self.log.error(e)
            self.session.rollback()
            raise HTTPError(
                HTTPStatus.UNPROCESSABLE_ENTITY, reason="Cannot add object to database."
            )
        self.set_status(HTTPStatus.CREATED)
        self.write_json(assignment)


@register_handler(
    path=r"\/api\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/?",
    version_specifier=VersionSpecifier.ALL,
)
class AssignmentObjectHandler(GraderBaseHandler):
    """Tornado Handler for http requests

    route: /lectures/{lecture_id}/assignments/{assignment_id}."""

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
        self.validate_parameters("recalc-scores")
        recalc_scores = self.get_argument("recalc-scores", None) == "true"
        body = tornado.escape.json_decode(self.request.body)
        assignment_model = AssignmentModel.from_dict(body)
        assignment = self.get_assignment(lecture_id, assignment_id)
        # Validate name
        assignment_with_name = (
            self.session.query(Assignment)
            .filter(
                Assignment.name == assignment_model.name,
                Assignment.deleted == DeleteState.active,
                Assignment.lectid == assignment.lectid,
            )
            .one_or_none()
        )

        if (assignment_with_name is not None) and (assignment_with_name.id != assignment_id):
            raise HTTPError(HTTPStatus.CONFLICT, reason="Assignment name is already being used")
        if (assignment_model.settings.max_submissions is not None) and (
            assignment_model.settings.max_submissions < 1
        ):
            raise HTTPError(HTTPStatus.BAD_REQUEST, reason="Max num submissions < 1!")
        validate_assignment_settings(assignment_model.settings)

        assignment.name = assignment_model.name
        assignment.status = assignment_model.status
        if (assignment_model.settings.autograde_type == "full_auto") and (
            assignment.properties is not None
        ):
            model = GradeBookModel.from_dict(json.loads(assignment.properties))
            _check_full_auto_grading(self, model)

        assignment.settings = assignment_model.settings

        # recalculate scores of assignment submissions
        if recalc_scores:
            submissions = self.get_all_submissions(assignment_id)
            role = Role()
            role.role = Scope.instructor
            for sub in submissions:
                late_submission_scaling = SubmissionHandler.calculate_late_submission_scaling(
                    assignment, sub.date, role
                )
                # change score if the scaling changed
                if sub.score_scaling != late_submission_scaling:
                    sub.score = late_submission_scaling * sub.grading_score
                    sub.score_scaling = late_submission_scaling

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
        assignment = self.get_assignment(lecture_id=lecture_id, assignment_id=assignment_id)
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

        if assignment.status in ["released", "complete"]:
            msg = "Cannot delete released or completed assignments!"
            raise HTTPError(HTTPStatus.CONFLICT, reason=msg)

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
    path=r"\/api\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/reset\/?",
    version_specifier=VersionSpecifier.ALL,
)
class AssignmentResetHandler(GraderBaseHandler):
    """Tornado Handler for http requests

    route: /lectures/{lecture_id}/assignments/{assignment_id}/reset."""

    @authorize([Scope.instructor, Scope.tutor, Scope.student])
    async def get(self, lecture_id: int, assignment_id: int):
        self.validate_parameters()
        lecture_id, assignment_id = parse_ids(lecture_id, assignment_id)
        assignment = self.get_assignment(lecture_id, assignment_id)

        grader_service_dir = Path(self.application.grader_service_dir)
        git_path_base = grader_service_dir.joinpath(
            "tmp", assignment.lecture.code, assignment.name, self.user.name
        )
        self.log.info(git_path_base)
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

        repo_path_release = self.construct_git_dir(
            GitRepoType.RELEASE, assignment.lecture, assignment
        )
        repo_path_user = self.construct_git_dir(GitRepoType.USER, assignment.lecture, assignment)

        self.duplicate_release_repo(
            repo_path_release=repo_path_release,
            repo_path_user=repo_path_user,
            assignment=assignment,
            message="Reset Assignment",
        )

        self.write_json(assignment)


@register_handler(
    path=r"\/api\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)"
    r"\/properties\/?",
    version_specifier=VersionSpecifier.ALL,
)
class AssignmentPropertiesHandler(GraderBaseHandler):
    """Tornado Handler for http requests

    route: /lectures/{lecture_id}/assignments/{assignment_id}/properties."""

    @authorize([Scope.student, Scope.tutor, Scope.instructor])
    async def get(self, lecture_id: int, assignment_id: int):
        """
        Returns the properties of a specific assignment.

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        :raises HTTPError: if assignment or their properties not found
        """
        lecture_id, assignment_id = parse_ids(lecture_id, assignment_id)

        self.validate_parameters()
        assignment = self.get_assignment(lecture_id, assignment_id)
        if assignment.properties is not None:
            if self.get_role(lecture_id).role == Scope.student:
                model = GradeBookModel.from_dict(json.loads(assignment.properties))
                for notebook in model.notebooks.values():
                    notebook.source_cells_dict = {}
                self.write(json.dumps(model.to_dict()))
            else:
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
        # Check if assignment contains no cells that
        # need manual grading if assignment is fully auto grade
        if assignment.settings.autograde_type == "full_auto":
            _check_full_auto_grading(self, model)

        assignment.properties = properties_string
        assignment.points = model.max_score
        self.session.commit()


def _check_full_auto_grading(self: GraderBaseHandler, model):
    """Check if the assignment notebook contains manually graded cells

    If cells are found, throw error.
    :param self: handler class
    :param model: the notebook which is being tested
    :return: void"""
    for nb in model.notebooks.values():
        if len(nb.task_cells_dict) > 0:
            msg = "Fully autograded notebook cannot contain task cells!"
            raise HTTPError(HTTPStatus.CONFLICT, reason=msg)
        grades = set(nb.grade_cells_dict.keys())
        solutions = set(nb.solution_cells_dict.keys())
        if len(grades & solutions) > 0:
            msg = "Fully autograded notebook cannot contain manually graded cells!"
            raise HTTPError(HTTPStatus.CONFLICT, reason=msg)
