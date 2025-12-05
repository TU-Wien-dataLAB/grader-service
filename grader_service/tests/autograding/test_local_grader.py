import copy
import json
import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
import traitlets.traitlets

from grader_service.autograding.local_grader import (
    LocalAutogradeExecutor,
    LocalAutogradeProcessExecutor,
)
from grader_service.orm import Assignment
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
    # Note: No need to patch `grader_service.autograding.local_grader.Autograde`,
    # as it is *not* directly called in the process executor's `_run` method.
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
        executor = LocalAutogradeProcessExecutor(
            grader_service_dir=str(tmp_path), submission=submission_123
        )
        yield executor


# =============== LocalAutogradeExecutor tests ===============


@patch("grader_service.convert.gradebook.models.GradeBookModel.from_dict")
@patch("grader_service.convert.gradebook.models.Notebook", autospec=True)
def test_local_autograde_start_outcome_on_success(
    mock_notebook, mock_gradebook, local_autograde_executor
):
    """Test the results of successfully calling `start`"""
    # Mock grades in the gradebook
    mock_notebook.score = 1
    mock_notebook_2 = copy.deepcopy(mock_notebook)
    mock_notebook_2.score = 2
    mock_gradebook.return_value.notebooks = {
        "notebook1": mock_notebook,  # score = 1
        "notebook2": mock_notebook_2,  # score = 2
    }

    local_autograde_executor.start()

    assert local_autograde_executor.submission.auto_status == AutoStatus.AUTOMATICALLY_GRADED
    assert local_autograde_executor.submission.grading_score == 1 + 2
    assert local_autograde_executor.submission.score == 1 + 2
    assert local_autograde_executor.session.commit.called


@patch("grader_service.autograding.local_grader.Autograde")
def test_local_autograde_start_outcome_on_autograde_failure(
    mock_autograde, local_autograde_executor
):
    """Test the results of calling `start` when autograding fails"""
    mock_autograde_instance = Mock()
    mock_autograde_instance.log = Mock()
    mock_autograde_instance.start.side_effect = PermissionError("Couldn't create file.")
    mock_autograde.return_value = mock_autograde_instance

    local_autograde_executor.start()

    # Verify _set_db_state() was called and the feedback status is set properly
    assert local_autograde_executor.submission.auto_status == AutoStatus.GRADING_FAILED
    assert local_autograde_executor.submission.score is None
    assert local_autograde_executor.session.commit.called
    # Verify logs were still captured despite the exception
    # Note: The submission in the db is not updated with the logs, because we mock the db session.
    assert local_autograde_executor.grading_logs == "Couldn't create file."
    mock_autograde_instance.log.removeHandler.assert_called_once()


@patch("grader_service.autograding.local_grader.Session", autospec=True)
def test_local_autograde_start_outcome_on_git_cmd_failure(
    mock_session_class, tmp_path, submission_123
):
    mock_session_class.object_session.return_value = Mock()
    executor = LocalAutogradeExecutor(grader_service_dir=str(tmp_path), submission=submission_123)

    with patch.object(executor.git_manager, "pull_submission") as git_pull:
        git_pull.side_effect = Exception("Git error")

        executor.start()

    assert executor.submission.auto_status == AutoStatus.GRADING_FAILED
    assert executor.grading_logs == "Git error"


def test_whitelist_pattern_combination(local_autograde_executor, submission_123):
    """Test that whitelist patterns of an assignment are combined correctly"""
    submission_123.assignment.properties = json.dumps(
        {"extra_files": ["*.txt", "*.csv", "Introduction to numpy.md"]}
    )
    submission_123.assignment.settings = {"allowed_files": ["*.py"]}

    patterns = local_autograde_executor._get_whitelist_patterns()

    expected_patterns = {"*.ipynb", "*.txt", "*.csv", "*.py", "Introduction to numpy.md"}
    assert patterns == expected_patterns


@patch(
    "grader_service.autograding.local_grader.LocalAutogradeExecutor.git_manager_class",
    autospec=True,
)
def test_file_matching_with_patterns(mock_git, tmp_path, submission_123):
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


@patch(
    "grader_service.autograding.local_grader.LocalAutogradeExecutor.git_manager_class",
    autospec=True,
)
def test_input_output_path_properties(mock_git, tmp_path, submission_123):
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
    input_leftover_file = Path(input_dir) / "test.txt"
    output_leftover_file = Path(output_dir) / "test.txt"
    input_leftover_file.touch()
    output_leftover_file.touch()

    # This should recreate empty input and output dirs.
    local_autograde_executor._clean_up_input_and_output_dirs()

    assert not os.path.exists(input_leftover_file)
    assert not os.path.exists(output_leftover_file)
    assert os.path.exists(input_dir)
    assert os.path.exists(output_dir)


def test_submission_logs_update(local_autograde_executor):
    """Test that submission logs are updated"""

    def side_effect():
        local_autograde_executor.grading_logs = "Test logs"

    local_autograde_executor._set_properties = MagicMock()
    local_autograde_executor._set_properties.side_effect = side_effect

    local_autograde_executor.start()

    assert local_autograde_executor.session.commit.called
    assert local_autograde_executor.session.merge.called
    # Note: the actual submission object in the db is not updated, because we mock the `session`.
    # TODO: Maybe save the submission to the db? Then we don't have to mock the session.
    sub_logs = local_autograde_executor.session.merge.call_args[0][0]
    assert sub_logs.logs == "Test logs"
    assert sub_logs.sub_id == 123


def test_timeout_function_default(local_autograde_executor):
    """Test default timeout function"""

    timeout = local_autograde_executor.cell_timeout
    assert timeout == 300  # Default timeout


@patch("grader_service.autograding.local_grader.Session")
@patch(
    "grader_service.autograding.local_grader.LocalAutogradeExecutor.git_manager_class",
    autospec=True,
)
def test_timeout_function_custom(mock_git, mock_session_class, tmp_path, submission_123):
    """Test custom timeout function"""

    custom_timeout = 720

    executor = LocalAutogradeExecutor(
        grader_service_dir=str(tmp_path),
        submission=submission_123,
        close_session=False,
        default_cell_timeout=custom_timeout,
    )

    timeout = executor.cell_timeout
    assert timeout == 720


def test_invalid_custom_default_timeout(tmp_path, submission_123):
    invalid_timeout = -1

    executor = LocalAutogradeExecutor(
        grader_service_dir=str(tmp_path), submission=submission_123, close_session=False
    )
    with pytest.raises(traitlets.traitlets.TraitError) as exc_info:
        executor.default_cell_timeout = invalid_timeout
    assert exc_info.value.args[0] == (
        f"Invalid default_cell_timeout value ({invalid_timeout}). "
        "Timeout values must satisfy: 0 < min_cell_timeout < default_cell_timeout < max_cell_timeout. "
        f"Got min={executor.min_cell_timeout}, default={invalid_timeout}, max={executor.max_cell_timeout}."
    )


def test_gradebook_writing(local_autograde_executor):
    """Test that gradebook is written correctly"""

    os.makedirs(local_autograde_executor.output_path, exist_ok=True)

    gradebook_content = '{"test": "data"}'
    local_autograde_executor._write_gradebook(gradebook_content)

    # Verify file creation and content
    gradebook_path = os.path.join(local_autograde_executor.output_path, "gradebook.json")
    assert os.path.exists(gradebook_path)

    with open(gradebook_path, "r") as f:
        content = f.read()
    assert content == gradebook_content


# =============== LocalAutogradeProcessExecutor tests ===============


def test_process_executor_start_success(process_executor):
    """Test successful execution of autograding process"""

    process_executor.start()

    # Verify the score and auto_status were set, and logs were captured
    assert "[AutogradeApp]" in process_executor.grading_logs
    assert process_executor.submission.auto_status == AutoStatus.AUTOMATICALLY_GRADED
    assert process_executor.submission.score == 0


@patch("grader_service.autograding.local_grader.subprocess.run", autospec=True)
def test_process_executor_run_failure(mock_run, process_executor):
    """Test handling of process execution failure in _run method"""
    mock_process = Mock()
    mock_process.returncode = 1
    mock_process.stderr = "Error: autograding failed"
    mock_run.return_value = mock_process
    os.makedirs(process_executor.output_path, exist_ok=True)

    with pytest.raises(RuntimeError, match="Process has failed execution!"):
        process_executor._run()

    # Verify subprocess was called with correct command and logs were captured
    expected_command = [
        "grader-convert",
        "autograde",
        "-i",
        process_executor.input_path,
        "-o",
        process_executor.output_path,
        "-p",
        "*.ipynb",
        "--ExecutePreprocessor.timeout=300",
    ]

    mock_run.assert_called_once_with(
        expected_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=None, text=True
    )
    assert process_executor.grading_logs == "Error: autograding failed"


@patch("grader_service.autograding.local_grader.subprocess.run", autospec=True)
def test_process_executor_run_subprocess_error(mock_run, process_executor):
    """Test handling of subprocess execution error in _run method"""
    mock_run.side_effect = OSError("Command not found")
    os.makedirs(process_executor.output_path, exist_ok=True)

    process_executor.start()

    # `start()` catches the exception, but should still log it
    assert "Command not found" in process_executor.grading_logs


def test_process_executor_inheritance():
    """Test that LocalAutogradeProcessExecutor properly inherits from LocalAutogradeExecutor"""
    assert issubclass(LocalAutogradeProcessExecutor, LocalAutogradeExecutor)
    assert hasattr(LocalAutogradeProcessExecutor, "convert_executable")
