import os
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from grader_service.autograding.local_feedback import (
    LocalFeedbackExecutor,
    LocalFeedbackProcessExecutor,
)
from grader_service.autograding.local_grader import LocalAutogradeExecutor
from grader_service.file_services.base_file_service import FileService
from grader_service.artifact_types import ArtifactType
from grader_service.orm.submission import AutoStatus, FeedbackStatus, ManualStatus


@pytest.fixture
def local_feedback_executor(tmp_path, submission_123):
    with (
        patch(
            "grader_service.autograding.local_grader.Session", autospec=True
        ) as mock_session_class,
        patch("grader_service.autograding.local_feedback.GenerateFeedback", autospec=True),
        patch(
            "grader_service.autograding.local_feedback.LocalFeedbackExecutor.file_service",
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
            "grader_service.autograding.local_feedback.LocalFeedbackExecutor.file_service",
            autospec=True,
        ),
    ):
        mock_session_class.object_session.return_value = Mock()
        executor = LocalFeedbackProcessExecutor(
            grader_service_dir=str(tmp_path), submission=submission_123
        )
        yield executor


# =============== LocalFeedbackExecutor tests ===============


@patch(
    "grader_service.autograding.local_feedback.LocalFeedbackExecutor.file_service", autospec=True
)
def test_input_output_artifact_types(mock_file_svc, grader_service, submission_123):
    """Test that input- and output-artifact types are correctly set."""

    submission_123.auto_status = AutoStatus.NOT_GRADED
    submission_123.manual_status = ManualStatus.MANUALLY_GRADED

    executor = LocalFeedbackExecutor(submission=submission_123)

    assert executor.input_artifact_type == ArtifactType.USER
    assert executor.output_artifact_type == ArtifactType.FEEDBACK


@patch(
    "grader_service.autograding.local_feedback.LocalFeedbackExecutor.file_service", autospec=True
)
def test_input_output_artifact_types_for_manually_graded_submission(
    mock_file_svc, grader_service, submission_123
):
    """Test that input artifact type falls back to USER for a manually graded submission."""

    submission_123.auto_status = AutoStatus.AUTOMATICALLY_GRADED

    executor = LocalFeedbackExecutor(submission=submission_123)

    assert executor.input_artifact_type == ArtifactType.AUTOGRADE
    assert executor.output_artifact_type == ArtifactType.FEEDBACK


@patch("grader_service.autograding.local_grader.Session", autospec=True)
@patch(
    "grader_service.autograding.local_feedback.LocalFeedbackExecutor.file_service", autospec=True
)
def test_input_output_path_properties(mock_file_svc, mock_session_cls, tmp_path, submission_123):
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


@pytest.mark.slow
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


def test_feedback_executor_inheritance(grader_service, submission_123):
    """Test that LocalFeedbackExecutor properly inherits from LocalAutogradeExecutor
    and has the correct input- and output-artifact types set."""
    assert issubclass(LocalFeedbackExecutor, LocalAutogradeExecutor)

    lfe = LocalFeedbackExecutor(
        grader_service_dir=grader_service.grader_service_dir, submission=submission_123
    )

    assert isinstance(lfe.file_service, FileService)
    assert lfe.input_artifact_type == ArtifactType.AUTOGRADE
    assert lfe.output_artifact_type == ArtifactType.FEEDBACK


def test_process_executor_inheritance():
    """Test that LocalFeedbackProcessExecutor properly inherits from LocalFeedbackExecutor"""
    assert issubclass(LocalFeedbackProcessExecutor, LocalFeedbackExecutor)
    assert hasattr(LocalFeedbackProcessExecutor, "convert_executable")
