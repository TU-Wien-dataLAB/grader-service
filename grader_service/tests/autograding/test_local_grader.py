import json
import os
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from grader_service.autograding.local_grader import (
    LocalAutogradeExecutor,
    LocalProcessAutogradeExecutor,
)
from grader_service.orm import Assignment, Lecture
from grader_service.orm.submission import AutoStatus


@pytest.fixture
def local_autograde_executor(tmp_path, submission_123):
    with (
        patch(
            "grader_service.autograding.local_grader.Session", autospec=True
        ) as mock_session_class,
        patch("grader_service.autograding.local_grader.Autograde", autospec=True),
        patch(
            "grader_service.autograding.local_grader.LocalAutogradeExecutor.git_manager_class",
            autospec=True,
        ),
    ):
        mock_session_class.object_session.return_value = Mock()
        yield LocalAutogradeExecutor(grader_service_dir=str(tmp_path), submission=submission_123)


@pytest.fixture
def process_executor(tmp_path, submission_123):
    with (
        patch(
            "grader_service.autograding.local_grader.Session", autospec=True
        ) as mock_session_class,
        patch(
            "grader_service.autograding.local_grader.LocalAutogradeExecutor.git_manager_class",
            autospec=True,
        ),
    ):
        mock_session_class.object_session.return_value = Mock()
        executor = LocalProcessAutogradeExecutor(
            grader_service_dir=str(tmp_path), submission=submission_123
        )
        yield executor


def test_whitelist_pattern_combination():
    """Test that whitelist patterns of an assignment are combined correctly"""
    assignment = Assignment(id=1)
    assignment.properties = json.dumps(
        {"extra_files": ["*.txt", "*.csv", "Introduction to numpy.md"]}
    )
    assignment.settings = {"allowed_files": ["*.py"]}

    expected_patterns = {"*.ipynb", "*.txt", "*.csv", "*.py", "Introduction to numpy.md"}
    patterns = assignment.get_whitelist_patterns()
    assert patterns == expected_patterns


@patch("grader_service.autograding.local_grader.Session", autospec=True)
@patch(
    "grader_service.autograding.local_grader.LocalAutogradeExecutor.git_manager_class",
    autospec=True,
)
def test_file_matching_with_patterns(mock_git, mock_session_class, tmp_path, submission_123):
    """Test that files are correctly matched against assignment whitelist patterns"""
    assignment = Assignment(id=1)
    assignment.properties = json.dumps({"extra_files": ["*/config"]})
    assignment.settings = {"allowed_files": ["*.py"]}

    submission_123.assignment = assignment

    executor = LocalAutogradeExecutor(
        grader_service_dir=str(tmp_path), submission=submission_123, close_session=False
    )
    assert executor.assignment.get_whitelist_patterns() == {"*.ipynb", "*/config", "*.py"}
    # Create test files in output directory
    os.makedirs(executor.output_path, exist_ok=True)
    test_dirs_and_files = [
        (executor.output_path, ["Ex1.ipynb", "output.txt", "weird name.py", "config"]),
        (executor.output_path + "/.git", ["config", "description", "HEAD"]),
        (executor.output_path + "/bar", ["Ex2.ipynb", "data.gz", "config"]),
    ]
    for root, filenames in test_dirs_and_files:
        os.makedirs(root, exist_ok=True)
        for f in filenames:
            (Path(root) / f).touch()

    # Get files to commit matching the whitelist patterns
    files_to_commit = executor._get_whitelisted_files()

    expected_files = {"Ex1.ipynb", "'weird name.py'", "bar/Ex2.ipynb", "bar/config"}
    assert set(files_to_commit) == expected_files


@patch("grader_service.autograding.local_grader.Session", autospec=True)
@patch(
    "grader_service.autograding.local_grader.LocalAutogradeExecutor.git_manager_class",
    autospec=True,
)
def test_input_output_path_properties(mock_git, mock_session_class, tmp_path, submission_123):
    """Test that input and output paths are correctly constructed"""
    expected_input = os.path.join(tmp_path, "convert_in", "submission_123")
    expected_output = os.path.join(tmp_path, "convert_out", "submission_123")

    executor = LocalAutogradeExecutor(grader_service_dir=str(tmp_path), submission=submission_123)

    assert executor.input_path == expected_input
    assert executor.output_path == expected_output


def test_directory_cleanup_on_init(local_autograde_executor, tmp_path):
    """Test that directories are cleaned up during initialization"""

    # Create pre-existing directories and some files in them
    input_dir = os.path.join(tmp_path, "convert_in", "submission_123")
    output_dir = os.path.join(tmp_path, "convert_out", "submission_123")
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    (Path(input_dir) / "test.txt").touch()
    (Path(output_dir) / "test.txt").touch()

    # This should clean the input and output dirs.
    local_autograde_executor.start()

    assert not os.path.exists(input_dir)
    assert not os.path.exists(output_dir)


def test_status_setting_on_success(local_autograde_executor):
    """Test that submission status is set correctly on success"""

    local_autograde_executor.start()

    assert local_autograde_executor.submission.auto_status == AutoStatus.AUTOMATICALLY_GRADED
    assert local_autograde_executor.session.commit.called


def test_status_setting_on_failure(local_autograde_executor):
    local_autograde_executor._run = Mock()
    local_autograde_executor._run.side_effect = PermissionError()

    local_autograde_executor.start()

    assert local_autograde_executor.submission.auto_status == AutoStatus.GRADING_FAILED
    assert local_autograde_executor.session.commit.called


def test_submission_logs_update(local_autograde_executor):
    """Test that submission logs are updated"""

    def side_effect():
        local_autograde_executor.grading_logs = "Test logs"

    local_autograde_executor._set_properties = MagicMock()
    local_autograde_executor._set_properties.side_effect = side_effect

    local_autograde_executor.start()

    assert local_autograde_executor.session.commit.called
    assert local_autograde_executor.session.merge.called
    # Note: the actual submission object is not updated, because we mock `session.merge`.
    sub_logs = local_autograde_executor.session.merge.call_args[0][0]
    assert sub_logs.logs == "Test logs"
    assert sub_logs.sub_id == 123


def test_timeout_function_default(local_autograde_executor):
    """Test default timeout function"""

    timeout = local_autograde_executor.timeout_func(Lecture())
    assert timeout == 360  # Default timeout


@patch("grader_service.autograding.local_grader.Session")
@patch(
    "grader_service.autograding.local_grader.LocalAutogradeExecutor.git_manager_class",
    autospec=True,
)
def test_timeout_function_custom(mock_git, mock_session_class, tmp_path, submission_123):
    """Test custom timeout function"""

    def custom_timeout(lecture):
        return 720

    executor = LocalAutogradeExecutor(
        grader_service_dir=str(tmp_path),
        submission=submission_123,
        close_session=False,
        timeout_func=custom_timeout,
    )

    timeout = executor.timeout_func(Lecture())
    assert timeout == 720


def test_gradebook_writing(local_autograde_executor):
    """Test that gradebook is written correctly"""

    # Create output directory
    os.makedirs(local_autograde_executor.output_path, exist_ok=True)

    # Write gradebook
    gradebook_content = '{"test": "data"}'
    local_autograde_executor._write_gradebook(gradebook_content)

    # Verify file was created
    gradebook_path = os.path.join(local_autograde_executor.output_path, "gradebook.json")
    assert os.path.exists(gradebook_path)

    # Verify content
    with open(gradebook_path, "r") as f:
        content = f.read()
    assert content == gradebook_content


def test_subprocess_error_handling(local_autograde_executor):
    """Test that subprocess errors are handled correctly"""

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = Exception("Command failed")

        with pytest.raises(Exception):
            local_autograde_executor._run_subprocess(
                "invalid_command", local_autograde_executor.output_path
            )

        assert "Command failed" in local_autograde_executor.grading_logs


# TODO: Add tests for the process executor
