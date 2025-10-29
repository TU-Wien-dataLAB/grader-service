import os
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from grader_service.autograding.local_feedback import (
    FeedbackGitSubmissionManager,
    LocalFeedbackExecutor,
    LocalFeedbackProcessExecutor,
)
from grader_service.autograding.local_grader import LocalAutogradeExecutor
from grader_service.handlers import GitRepoType
from grader_service.orm.submission import FeedbackStatus


@pytest.fixture
def local_feedback_executor(tmp_path, submission_123):
    with (
        patch(
            "grader_service.autograding.local_grader.Session", autospec=True
        ) as mock_session_class,
        patch("grader_service.autograding.local_feedback.GenerateFeedback", autospec=True),
        patch(
            "grader_service.autograding.local_feedback.LocalFeedbackExecutor.git_manager_class",
            autospec=True,
        ),
    ):
        mock_session_class.object_session.return_value = Mock()
        yield LocalFeedbackExecutor(grader_service_dir=str(tmp_path), submission=submission_123)


@pytest.fixture
def process_executor(tmp_path, submission_123):
    # Note: No need to patch `grader_service.autograding.local_feedback.GenerateFeedback`,
    # as it is not directly called in the process executor's `_run` method.
    with (
        patch(
            "grader_service.autograding.local_grader.Session", autospec=True
        ) as mock_session_class,
        patch(
            "grader_service.autograding.local_feedback.LocalFeedbackExecutor.git_manager_class",
            autospec=True,
        ),
    ):
        mock_session_class.object_session.return_value = Mock()
        executor = LocalFeedbackProcessExecutor(
            grader_service_dir=str(tmp_path), submission=submission_123
        )
        yield executor


# =============== LocalFeedbackExecutor tests ===============


@patch("grader_service.autograding.local_grader.Session", autospec=True)
@patch(
    "grader_service.autograding.local_feedback.LocalFeedbackExecutor.git_manager_class",
    autospec=True,
)
def test_input_output_path_properties(mock_git, mock_session_class, tmp_path, submission_123):
    """Test that input and output paths are correctly constructed for feedback generation"""
    expected_input = os.path.join(tmp_path, "convert_in", f"feedback_{submission_123.id}")
    expected_output = os.path.join(tmp_path, "convert_out", f"feedback_{submission_123.id}")

    executor = LocalFeedbackExecutor(grader_service_dir=str(tmp_path), submission=submission_123)

    assert executor.input_path == expected_input
    assert executor.output_path == expected_output


def test_get_whitelisted_patterns(local_feedback_executor):
    """Test that _get_whitelist_patterns returns only html files (ignoring other whitelist patterns)"""
    files = local_feedback_executor._get_whitelist_patterns()
    assert files == {"*.html"}


def test_set_properties(local_feedback_executor):
    """Test that _set_properties does nothing (no-op for feedback generation)"""
    local_feedback_executor._set_properties()

    local_feedback_executor.session.merge.assert_not_called()


def test_directory_cleanup_on_init(local_feedback_executor, tmp_path):
    """Test that directories are cleaned up during initialization"""
    # Create pre-existing directories and some files in them
    input_dir = os.path.join(
        tmp_path, "convert_in", f"feedback_{local_feedback_executor.submission.id}"
    )
    output_dir = os.path.join(
        tmp_path, "convert_out", f"feedback_{local_feedback_executor.submission.id}"
    )
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    (Path(input_dir) / "test.txt").touch()
    (Path(output_dir) / "test.txt").touch()

    # This should clean the input and output dirs
    local_feedback_executor.start()

    assert not os.path.exists(input_dir)
    assert not os.path.exists(output_dir)


@patch("grader_service.autograding.local_feedback.GenerateFeedback")
def test_run_successful_feedback_generation(mock_gen_feedback, local_feedback_executor):
    """Test successful feedback generation process"""
    # Setup mock GenerateFeedback instance
    mock_feedback_instance = Mock()
    mock_gen_feedback.return_value = mock_feedback_instance

    local_feedback_executor.start()

    mock_gen_feedback.assert_called_once_with(
        local_feedback_executor.input_path,
        local_feedback_executor.output_path,
        "*.ipynb",
        assignment_settings=local_feedback_executor.assignment.settings,
    )
    mock_feedback_instance.start.assert_called_once()

    # Verify _set_db_state() was called and the feedback status is set properly
    local_feedback_executor.session.commit.assert_called()
    assert local_feedback_executor.submission.feedback_status == FeedbackStatus.GENERATED


@patch("grader_service.autograding.local_feedback.GenerateFeedback")
def test_run_feedback_generation_with_exception(mock_generate_feedback, local_feedback_executor):
    """Test feedback generation failing"""
    # Setup mock feedback generator that raises an exception
    mock_feedback_instance = Mock()
    mock_feedback_instance.start.side_effect = RuntimeError("Generation failed")
    mock_generate_feedback.return_value = mock_feedback_instance

    # Run the feedback generation; the exception should be caught
    local_feedback_executor.start()

    # Verify logs were still captured despite the exception
    assert local_feedback_executor.grading_logs == "Generation failed"
    # Verify _set_db_state() was called and the feedback status is set properly
    local_feedback_executor.session.commit.assert_called()
    assert local_feedback_executor.submission.feedback_status == FeedbackStatus.GENERATION_FAILED


def test_gradebook_writing(local_feedback_executor):
    """Test that gradebook is written correctly"""
    os.makedirs(local_feedback_executor.output_path, exist_ok=True)

    gradebook_content = '{"test": "data", "notebooks": {}}'
    local_feedback_executor._write_gradebook(gradebook_content)

    gradebook_path = os.path.join(local_feedback_executor.output_path, "gradebook.json")
    assert os.path.exists(gradebook_path)

    with open(gradebook_path, "r") as f:
        content = f.read()
    assert content == gradebook_content


# =============== LocalFeedbackProcessExecutor tests ===============


def test_process_executor_start_success(process_executor):
    """Test successful execution of feedback generation process"""
    process_executor.start()

    # Verify submission feedback status was set
    assert process_executor.submission.feedback_status == FeedbackStatus.GENERATED


def test_process_executor_start_failure(process_executor):
    """Test handling of errors in `start` method"""
    process_executor._write_gradebook = Mock()
    process_executor._write_gradebook.side_effect = PermissionError("Cannot write gradebook")

    process_executor.start()

    # Verify submission feedback status was set
    assert "Cannot write gradebook" in process_executor.grading_logs
    assert process_executor.submission.feedback_status == FeedbackStatus.GENERATION_FAILED


@patch("grader_service.autograding.local_feedback.subprocess.run", autospec=True)
def test_process_executor_run_failure(mock_run, process_executor):
    """Test handling of process execution failure in _run method"""
    mock_process = Mock()
    mock_process.returncode = 1
    mock_process.stderr = "Error: something went wrong"
    mock_run.return_value = mock_process
    os.makedirs(process_executor.output_path, exist_ok=True)

    with pytest.raises(RuntimeError, match="Process has failed execution!"):
        process_executor._run()

    # Verify subprocess was called with correct command
    expected_command = [
        "grader-convert",
        "generate_feedback",
        "-i",
        process_executor.input_path,
        "-o",
        process_executor.output_path,
        "-p",
        "*.ipynb",
    ]

    mock_run.assert_called_once_with(
        expected_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=None, text=True
    )


@patch("grader_service.autograding.local_feedback.subprocess.run", autospec=True)
def test_process_executor_run_subprocess_error(mock_run, process_executor):
    """Test handling of subprocess execution error in _run method"""
    mock_run.side_effect = OSError("Command not found")
    os.makedirs(process_executor.output_path, exist_ok=True)

    with pytest.raises(OSError, match="Command not found"):
        process_executor._run()


def test_feedback_executor_inheritance(tmp_path, submission_123):
    """Test that LocalFeedbackExecutor properly inherits from LocalAutogradeExecutor
    and uses the FeedbackGitSubmissionManager for git operations"""
    assert issubclass(LocalFeedbackExecutor, LocalAutogradeExecutor)

    gfe = LocalFeedbackExecutor(grader_service_dir=str(tmp_path), submission=submission_123)

    assert isinstance(gfe.git_manager, FeedbackGitSubmissionManager)
    assert gfe.git_manager.input_repo_type == GitRepoType.AUTOGRADE
    assert gfe.git_manager.output_repo_type == GitRepoType.FEEDBACK


def test_process_executor_inheritance():
    """Test that LocalFeedbackProcessExecutor properly inherits from LocalFeedbackExecutor"""
    assert issubclass(LocalFeedbackProcessExecutor, LocalFeedbackExecutor)
    assert hasattr(LocalFeedbackProcessExecutor, "convert_executable")
