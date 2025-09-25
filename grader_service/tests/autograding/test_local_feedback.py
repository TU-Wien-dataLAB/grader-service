import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from grader_service.autograding.local_feedback import (
    FeedbackGitSubmissionManager,
    GenerateFeedbackExecutor,
    GenerateFeedbackProcessExecutor,
)
from grader_service.autograding.local_grader import LocalAutogradeExecutor
from grader_service.orm.submission import FeedbackStatus


@pytest.fixture
def feedback_executor(tmp_path, submission_123):
    with (
        patch(
            "grader_service.autograding.local_grader.Session", autospec=True
        ) as mock_session_class,
        patch("grader_service.autograding.local_feedback.GenerateFeedback", autospec=True),
        patch(
            "grader_service.autograding.local_feedback.GenerateFeedbackExecutor.git_manager_class",
            autospec=True,
        ),
    ):
        mock_session_class.object_session.return_value = Mock()
        yield GenerateFeedbackExecutor(grader_service_dir=str(tmp_path), submission=submission_123)


@pytest.fixture
def process_executor(tmp_path, submission_123):
    with (
        patch(
            "grader_service.autograding.local_grader.Session", autospec=True
        ) as mock_session_class,
        patch(
            "grader_service.autograding.local_feedback.GenerateFeedbackProcessExecutor."
            "git_manager_class",
            autospec=True,
        ),
    ):
        mock_session_class.object_session.return_value = Mock()
        executor = GenerateFeedbackProcessExecutor(
            grader_service_dir=str(tmp_path), submission=submission_123
        )
        yield executor


@patch("grader_service.autograding.local_grader.Session", autospec=True)
@patch(
    "grader_service.autograding.local_feedback.GenerateFeedbackExecutor.git_manager_class",
    autospec=True,
)
def test_input_output_path_properties(mock_git, mock_session_class, tmp_path, submission_123):
    """Test that input and output paths are correctly constructed for feedback generation"""
    expected_input = os.path.join(tmp_path, "convert_in", f"feedback_{submission_123.id}")
    expected_output = os.path.join(tmp_path, "convert_out", f"feedback_{submission_123.id}")

    executor = GenerateFeedbackExecutor(grader_service_dir=str(tmp_path), submission=submission_123)

    assert executor.input_path == expected_input
    assert executor.output_path == expected_output


def test_get_whitelisted_files(feedback_executor):
    """Test that _get_whitelisted_files returns all files (no filtering for feedback)"""
    files = feedback_executor._get_whitelisted_files()
    assert files == ["."]


def test_set_properties(feedback_executor):
    """Test that _set_properties does nothing (no-op for feedback generation)"""
    # This method should not raise any exceptions and should do nothing
    feedback_executor._set_properties()


def test_directory_cleanup_on_init(feedback_executor, tmp_path):
    """Test that directories are cleaned up during initialization"""
    # Create pre-existing directories and some files in them
    input_dir = os.path.join(tmp_path, "convert_in", f"feedback_{feedback_executor.submission.id}")
    output_dir = os.path.join(
        tmp_path, "convert_out", f"feedback_{feedback_executor.submission.id}"
    )
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    (Path(input_dir) / "test.txt").touch()
    (Path(output_dir) / "test.txt").touch()

    # This should clean the input and output dirs
    feedback_executor.start()

    assert not os.path.exists(input_dir)
    assert not os.path.exists(output_dir)


@patch("grader_service.autograding.local_feedback.GenerateFeedback")
def test_run_successful_feedback_generation(mock_gen_feedback, feedback_executor):
    """Test successful feedback generation process"""
    # Setup mock feedback generator
    mock_feedback_instance = Mock()
    mock_gen_feedback.return_value = mock_feedback_instance
    mock_feedback_instance.log = Mock()

    feedback_executor.start()

    mock_gen_feedback.assert_called_once_with(
        feedback_executor.input_path,
        feedback_executor.output_path,
        "*.ipynb",
        assignment_settings=feedback_executor.assignment.settings,
    )
    mock_feedback_instance.start.assert_called_once()
    mock_feedback_instance.log.addHandler.assert_called_once()
    mock_feedback_instance.log.removeHandler.assert_called_once()

    assert feedback_executor.grading_logs is not None
    # Verify _set_db_state() was called and the feedback status is set properly
    feedback_executor.session.commit.assert_called()
    assert feedback_executor.submission.feedback_status == FeedbackStatus.GENERATED


@patch("grader_service.autograding.local_feedback.GenerateFeedback")
def test_run_feedback_generation_with_exception(mock_generate_feedback, feedback_executor):
    """Test feedback generation failing"""
    # Setup mock feedback generator that raises an exception
    mock_feedback_instance = Mock()
    mock_generate_feedback.return_value = mock_feedback_instance
    mock_feedback_instance.log = Mock()
    mock_feedback_instance.start.side_effect = RuntimeError("Generation failed")

    # Run the feedback generation; the exception should be caught
    feedback_executor.start()

    # Verify logs were still captured despite the exception
    assert feedback_executor.grading_logs is not None
    mock_feedback_instance.log.removeHandler.assert_called_once()
    # Verify _set_db_state() was called and the feedback status is set properly
    feedback_executor.session.commit.assert_called()
    assert feedback_executor.submission.feedback_status == FeedbackStatus.GENERATION_FAILED


def test_gradebook_writing(feedback_executor):
    """Test that gradebook is written correctly"""
    os.makedirs(feedback_executor.output_path, exist_ok=True)

    gradebook_content = '{"test": "data", "notebooks": {}}'
    feedback_executor._write_gradebook(gradebook_content)

    gradebook_path = os.path.join(feedback_executor.output_path, "gradebook.json")
    assert os.path.exists(gradebook_path)

    with open(gradebook_path, "r") as f:
        content = f.read()
    assert content == gradebook_content


def test_process_executor_run_success(process_executor):
    """Test successful execution of feedback generation process"""
    # Mock subprocess execution
    mock_process = Mock()
    mock_process.returncode = 0
    mock_process.stderr.read.return_value.decode.return_value = "Process completed successfully"
    process_executor._run_subprocess = Mock(return_value=mock_process)
    os.makedirs(process_executor.output_path, exist_ok=True)

    process_executor._run()

    # Verify subprocess was called with correct command and logs were captured
    expected_command = (
        f'grader-convert generate_feedback -i "{process_executor.input_path}" '
        f'-o "{process_executor.output_path}" -p "*.ipynb"'
    )
    process_executor._run_subprocess.assert_called_once_with(expected_command, None)
    assert process_executor.grading_logs == "Process completed successfully"


def test_process_executor_run_failure(process_executor):
    """Test handling of process execution failure"""
    # Mock subprocess execution with failure
    mock_process = Mock()
    mock_process.returncode = 1
    mock_process.stderr.read.return_value.decode.return_value = "Error: something went wrong"
    process_executor._run_subprocess = Mock(return_value=mock_process)
    os.makedirs(process_executor.output_path, exist_ok=True)

    with pytest.raises(RuntimeError, match="Process has failed execution!"):
        process_executor._run()

    # Verify subprocess was called with correct command and logs were captured
    expected_command = (
        f'grader-convert generate_feedback -i "{process_executor.input_path}" '
        f'-o "{process_executor.output_path}" -p "*.ipynb"'
    )
    process_executor._run_subprocess.assert_called_once_with(expected_command, None)
    assert process_executor.grading_logs == "Error: something went wrong"


def test_process_executor_subprocess_error(process_executor):
    """Test handling of subprocess execution error"""
    # Mock subprocess execution that raises an exception
    process_executor._run_subprocess = Mock(side_effect=OSError("Command not found"))
    os.makedirs(process_executor.output_path, exist_ok=True)

    # Run the process and expect exception
    with pytest.raises(OSError, match="Command not found"):
        process_executor._run()


def test_feedback_executor_inheritance(tmp_path, submission_123):
    """Test that GenerateFeedbackExecutor properly inherits from LocalAutogradeExecutor
    and uses the FeedbackGitSubmissionManager for git operations"""
    assert issubclass(GenerateFeedbackExecutor, LocalAutogradeExecutor)

    gfe = GenerateFeedbackExecutor(grader_service_dir=str(tmp_path), submission=submission_123)

    assert isinstance(gfe.git_manager, FeedbackGitSubmissionManager)
    assert gfe.git_manager.input_repo_type.name == "AUTOGRADE"
    assert gfe.git_manager.output_repo_type.name == "FEEDBACK"


def test_process_executor_inheritance():
    """Test that GenerateFeedbackProcessExecutor properly inherits from GenerateFeedbackExecutor"""
    assert issubclass(GenerateFeedbackProcessExecutor, GenerateFeedbackExecutor)
    assert hasattr(GenerateFeedbackProcessExecutor, "convert_executable")
