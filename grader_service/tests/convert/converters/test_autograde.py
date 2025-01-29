import logging
import shutil
from unittest.mock import patch

from grader_service.api.models.assignment_settings import AssignmentSettings
from grader_service.tests.convert.converters import _create_input_output_dirs
from grader_service.convert.converters import GenerateAssignment, Autograde


def test_autograde(tmp_path):
    input_dir, output_dir = _create_input_output_dirs(tmp_path, ["simple.ipynb"])

    GenerateAssignment(
        input_dir=str(input_dir),
        output_dir=str(output_dir),
        file_pattern="*.ipynb",
        assignment_settings=AssignmentSettings(),
        config=None
    ).start()

    assert (output_dir / "simple.ipynb").exists()
    assert (output_dir / "gradebook.json").exists()

    output_dir2 = tmp_path / "output_dir2"
    output_dir2.mkdir()
    shutil.copyfile(output_dir / "gradebook.json", output_dir2 / "gradebook.json")
    assert (output_dir2 / "gradebook.json").exists()

    from nbclient.client import NotebookClient
    with patch.object(NotebookClient, "kernel_name", "python3"):
        Autograde(
            input_dir=str(output_dir),
            output_dir=str(output_dir2),
            file_pattern="*.ipynb",
            assignment_settings=AssignmentSettings(),
            config=None
        ).start()

    assert (output_dir2 / "simple.ipynb").exists()
    assert (output_dir2 / "gradebook.json").exists()


def test_autograde_copy_with_all_files(tmp_path):
    input_dir, output_dir = _create_input_output_dirs(tmp_path, ["simple.ipynb"])
    test_file = input_dir / "test.txt"
    test_file.touch()
    assert test_file.exists()

    GenerateAssignment(
        input_dir=str(input_dir),
        output_dir=str(output_dir),
        file_pattern="*.ipynb",
        assignment_settings=AssignmentSettings(allowed_files=["*"]),
        config=None
    ).start()

    assert (output_dir / "simple.ipynb").exists()
    assert (output_dir / "gradebook.json").exists()
    assert (output_dir / "test.txt").exists()

    output_dir2 = tmp_path / "output_dir2"
    output_dir2.mkdir()
    shutil.copyfile(output_dir / "gradebook.json", output_dir2 / "gradebook.json")
    assert (output_dir2 / "gradebook.json").exists()

    from nbclient.client import NotebookClient
    with patch.object(NotebookClient, "kernel_name", "python3"):
        Autograde(
            input_dir=str(output_dir),
            output_dir=str(output_dir2),
            file_pattern="*.ipynb",
            assignment_settings=AssignmentSettings(allowed_files=["*"]),
            config=None
        ).start()

    assert (output_dir2 / "simple.ipynb").exists()
    assert (output_dir2 / "gradebook.json").exists()
    assert (output_dir2 / "test.txt").exists()


def test_generate_assignment_copy_with_dirs(tmp_path):
    input_dir, output_dir = _create_input_output_dirs(tmp_path, ["simple.ipynb"])

    dir_1 = input_dir / "dir_1"
    dir_2 = dir_1 / "dir_2"
    dir_3 = dir_2 / "dir_3"
    dir_3.mkdir(parents=True)
    assert dir_3.exists()

    test_file = dir_3 / "test.txt"
    test_file.touch()
    assert test_file.exists()

    GenerateAssignment(
        input_dir=str(input_dir),
        output_dir=str(output_dir),
        file_pattern="*.ipynb",
        assignment_settings=AssignmentSettings(allowed_files=["*"]),
        config=None
    ).start()

    assert (output_dir / "simple.ipynb").exists()
    assert (output_dir / "gradebook.json").exists()
    assert (output_dir / "dir_1").exists()
    assert (output_dir / "dir_1/dir_2").exists()
    assert (output_dir / "dir_1/dir_2/dir_3").exists()
    assert (output_dir / "dir_1/dir_2/dir_3/test.txt").exists()

    output_dir2 = tmp_path / "output_dir2"
    output_dir2.mkdir()
    shutil.copyfile(output_dir / "gradebook.json", output_dir2 / "gradebook.json")
    assert (output_dir2 / "gradebook.json").exists()

    from nbclient.client import NotebookClient
    with patch.object(NotebookClient, "kernel_name", "python3"):
        Autograde(
            input_dir=str(output_dir),
            output_dir=str(output_dir2),
            file_pattern="*.ipynb",
            assignment_settings=AssignmentSettings(allowed_files=["*"]),
            config=None
        ).start()

    assert (output_dir2 / "simple.ipynb").exists()
    assert (output_dir2 / "gradebook.json").exists()
    assert (output_dir2 / "dir_1").exists()
    assert (output_dir2 / "dir_1/dir_2").exists()
    assert (output_dir2 / "dir_1/dir_2/dir_3").exists()
    assert (output_dir2 / "dir_1/dir_2/dir_3/test.txt").exists()

