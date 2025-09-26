import copy
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
        executor = LocalProcessAutogradeExecutor(
            grader_service_dir=str(tmp_path), submission=submission_123
        )
        yield executor


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


def test_local_autograde_start_outcome_on_failure(local_autograde_executor):
    """Test the results of calling `start` when autograding fails"""
    local_autograde_executor._run = Mock()
    local_autograde_executor._run.side_effect = PermissionError()

    local_autograde_executor.start()

    assert local_autograde_executor.submission.auto_status == AutoStatus.GRADING_FAILED
    assert local_autograde_executor.submission.score is None
    assert local_autograde_executor.session.commit.called


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

    os.makedirs(local_autograde_executor.output_path, exist_ok=True)

    gradebook_content = '{"test": "data"}'
    local_autograde_executor._write_gradebook(gradebook_content)

    # Verify file creation and content
    gradebook_path = os.path.join(local_autograde_executor.output_path, "gradebook.json")
    assert os.path.exists(gradebook_path)

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
        # TODO: Improve this test after rewriting _run_subprocess
        assert "Command failed" in local_autograde_executor.grading_logs


def test_process_executor_start_success(process_executor):
    """Test successful execution of autograding process"""

    process_executor.start()

    # Verify the score and auto_status were set, and logs were captured
    assert "[AutogradeApp]" in process_executor.grading_logs
    assert process_executor.submission.auto_status == AutoStatus.AUTOMATICALLY_GRADED
    assert process_executor.submission.score == 0


def test_process_executor_run_failure(process_executor):
    """Test handling of process execution failure in _run method"""
    mock_process = Mock()
    mock_process.returncode = 1
    mock_process.stderr = "Error: autograding failed"
    process_executor._run_subprocess = Mock(return_value=mock_process)
    os.makedirs(process_executor.output_path, exist_ok=True)

    with pytest.raises(RuntimeError, match="Process has failed execution!"):
        process_executor._run()

    # Verify subprocess was called with correct command and logs were captured
    expected_command = (
        f'grader-convert autograde -i "{process_executor.input_path}" '
        f'-o "{process_executor.output_path}" -p "*.ipynb" '
        f"--ExecutePreprocessor.timeout=360"
    )
    process_executor._run_subprocess.assert_called_once_with(expected_command, None)
    assert process_executor.grading_logs == "Error: autograding failed"


def test_process_executor_run_subprocess_error(process_executor):
    """Test handling of subprocess execution error in _run method"""
    process_executor._run_subprocess = Mock(side_effect=OSError("Command not found"))
    os.makedirs(process_executor.output_path, exist_ok=True)

    with pytest.raises(OSError, match="Command not found"):
        process_executor._run()


def test_process_executor_inheritance():
    """Test that LocalProcessAutogradeExecutor properly inherits from LocalAutogradeExecutor"""
    assert issubclass(LocalProcessAutogradeExecutor, LocalAutogradeExecutor)
    assert hasattr(LocalProcessAutogradeExecutor, "convert_executable")
