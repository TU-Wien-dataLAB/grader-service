import pytest

from grader_service.orm import Assignment, Lecture, Submission, User
from grader_service.orm.submission_properties import SubmissionProperties


@pytest.fixture
def submission_123():
    submission = Submission()
    submission.id = 123
    submission.assignment = Assignment(id=1, properties='{"notebooks": {}}')
    submission.assignment.lecture = Lecture(code="LEC_01")
    submission.assignment.settings.allowed_files = []
    submission.user = User(name="test_user")
    submission.properties = SubmissionProperties(properties='{"notebooks": {}}')
    submission.score_scaling = 1

    yield submission
