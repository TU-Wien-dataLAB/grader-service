import shutil
from unittest.mock import patch

from nbclient.client import NotebookClient

from grader_service.api.models.assignment_settings import AssignmentSettings
from grader_service.convert.converters import Autograde
from grader_service.tests.convert.converters import (
    _create_input_output_dirs,
    _generate_test_assignment,
)


def test_autograde(tmp_path):
    input_dir, output_dir = _create_input_output_dirs(tmp_path, ["simple.ipynb"])

    _generate_test_assignment(input_dir, output_dir)

    assert (output_dir / "simple.ipynb").exists()
    assert (output_dir / "gradebook.json").exists()

    output_dir2 = tmp_path / "output_dir2"
    output_dir2.mkdir()

    # The `gradebook.json` has to be copied manually so that the Autograde converter can keep track
    # of which files were present originally. (In real life, `gradebook.json` would be copied
    # by LocalAutogradeExecutor.)
    shutil.copyfile(output_dir / "gradebook.json", output_dir2 / "gradebook.json")

    with patch.object(NotebookClient, "kernel_name", "python3"):
        Autograde(
            input_dir=str(output_dir),
            output_dir=str(output_dir2),
            file_pattern="*.ipynb",
            assignment_settings=AssignmentSettings(),
            config=None,
        ).start()

    assert (output_dir2 / "simple.ipynb").exists()
    assert (output_dir2 / "gradebook.json").exists()


def test_autograde_copy_with_all_files(tmp_path):
    input_dir, output_dir = _create_input_output_dirs(tmp_path, ["simple.ipynb"])

    _generate_test_assignment(
        input_dir, output_dir, assignment_settings_kwargs={"allowed_files": ["*"]}
    )

    test_file = output_dir / "test.txt"
    test_file.touch()

    output_dir2 = tmp_path / "output_dir2"
    output_dir2.mkdir()
    shutil.copyfile(output_dir / "gradebook.json", output_dir2 / "gradebook.json")

    with patch.object(NotebookClient, "kernel_name", "python3"):
        Autograde(
            input_dir=str(output_dir),
            output_dir=str(output_dir2),
            file_pattern="*.ipynb",
            assignment_settings=AssignmentSettings(allowed_files=["*"]),
            config=None,
        ).start()

    assert (output_dir2 / "simple.ipynb").exists()
    assert (output_dir2 / "gradebook.json").exists()
    assert (output_dir2 / "test.txt").exists()


def test_autograde_copy_with_dirs(tmp_path):
    input_dir, output_dir = _create_input_output_dirs(tmp_path, ["simple.ipynb"])

    dir_1 = input_dir / "dir_1"
    dir_2 = dir_1 / "dir_2"
    dir_3 = dir_2 / "dir_3"
    dir_3.mkdir(parents=True)

    test_file = dir_3 / "test.txt"
    test_file.touch()

    _generate_test_assignment(
        input_dir, output_dir, assignment_settings_kwargs={"allowed_files": ["*"]}
    )

    assert (output_dir / "simple.ipynb").exists()
    assert (output_dir / "gradebook.json").exists()
    assert (output_dir / "dir_1/dir_2/dir_3/test.txt").exists()

    output_dir2 = tmp_path / "output_dir2"
    output_dir2.mkdir()
    shutil.copyfile(output_dir / "gradebook.json", output_dir2 / "gradebook.json")

    with patch.object(NotebookClient, "kernel_name", "python3"):
        Autograde(
            input_dir=str(output_dir),
            output_dir=str(output_dir2),
            file_pattern="*.ipynb",
            assignment_settings=AssignmentSettings(allowed_files=["*"]),
            config=None,
        ).start()

    assert (output_dir2 / "simple.ipynb").exists()
    assert (output_dir2 / "gradebook.json").exists()
    assert (output_dir2 / "dir_1").exists()
    assert (output_dir2 / "dir_1/dir_2").exists()
    assert (output_dir2 / "dir_1/dir_2/dir_3").exists()
    assert (output_dir2 / "dir_1/dir_2/dir_3/test.txt").exists()


def test_autograde_with_student_notebooks_copied_over(tmp_path):
    """Regression test: When assignment's allowed_files contain '*.ipynb', then notebooks created
    by the student should also be copied over."""
    input_dir, output_dir = _create_input_output_dirs(tmp_path, ["simple.ipynb"])

    _generate_test_assignment(input_dir, output_dir)

    student_nb = output_dir / "student.ipynb"
    student_nb.touch()

    output_dir2 = tmp_path / "output_dir2"
    output_dir2.mkdir()
    shutil.copyfile(output_dir / "gradebook.json", output_dir2 / "gradebook.json")

    with (
        patch.object(NotebookClient, "kernel_name", "python3"),
        patch(
            "grader_service.convert.converters.autograde.Autograde.convert_single_notebook"
        ) as convert_mock,
    ):
        Autograde(
            input_dir=str(output_dir),
            output_dir=str(output_dir2),
            file_pattern="*.ipynb",
            assignment_settings=AssignmentSettings(allowed_files=["*.ipynb"]),
            config=None,
        ).start()

    assert (output_dir2 / "simple.ipynb").exists()
    assert (output_dir2 / "gradebook.json").exists()
    assert (output_dir2 / "student.ipynb").exists()

    assert convert_mock.call_count == 2  # `convert_single_notebook` was called for both notebooks
