from unittest.mock import MagicMock, patch

import pytest

from grader_service.autograding.local_grader import LocalAutogradeExecutor
from grader_service.orm import Submission
from grader_service.api.models.assignment_settings import AssignmentSettings


@pytest.fixture
def local_autograde_executor():
    submission = Submission()
    submission.assignment = MagicMock()
    submission.id = 42

    yield LocalAutogradeExecutor(grader_service_dir="foo", submission=submission)


def test_get_whitelist_patterns(local_autograde_executor):
    local_autograde_executor.assignment.properties = '{"extra_files": ["Introduction to numpy.md"]}'
    local_autograde_executor.assignment.settings = AssignmentSettings(
        allowed_files=["*.py", "*.ipynb"]
    )

    assert local_autograde_executor._get_whitelist_patterns() == {
        "*.py",
        "*.ipynb",
        "Introduction to numpy.md",
    }


@patch("grader_service.autograding.local_grader.os.walk", autospec=True)
def test_get_files_to_commit(mock_walk, local_autograde_executor):
    mock_walk.return_value = [
        (
            "foo/convert_out/submission_42",
            [".git", "bar"],
            ["Ex1.ipynb", "output.txt", "weird name.py", "config"],
        ),
        ("foo/convert_out/submission_42/.git", ["refs"], ["config", "description", "HEAD"]),
        ("foo/convert_out/submission_42/.git/refs", ["heads", "tags"], []),
        ("foo/convert_out/submission_42/bar", [], ["Ex2.ipynb", "data.gz", "config"]),
    ]

    assert local_autograde_executor._get_files_to_commit({"*.ipynb", "*/config", "*.py"}) == [
        "Ex1.ipynb",
        "'weird name.py'",
        "bar/Ex2.ipynb",
        "bar/config",
    ]
