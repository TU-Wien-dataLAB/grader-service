from unittest.mock import Mock

import pytest

from grader_service.orm import Assignment, Lecture


@pytest.fixture
def submission_123():
    submission = Mock()
    submission.id = 123
    submission.assignment = Assignment(id=1, properties='{"notebooks": {}}')
    submission.assignment.lecture = Lecture(code="LEC_01")
    submission.assignment.settings.allowed_files = []
    submission.user.name = "test_user"
    submission.properties.properties = '{"notebooks": {}}'
    submission.score_scaling = 1

    yield submission
