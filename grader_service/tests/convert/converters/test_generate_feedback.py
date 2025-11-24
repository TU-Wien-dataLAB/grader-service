import os
import shutil

from grader_service.api.models.assignment_settings import AssignmentSettings
from grader_service.convert.converters import GenerateFeedback
from grader_service.tests.convert.converters import (
    _autograde_test_submission,
    _create_input_output_dirs,
    _generate_test_submission,
)


def test_generate_feedback(tmp_path):
    input_dir, output_dir = _create_input_output_dirs(
        tmp_path, ["simple.ipynb", "test.ipynb", "assignment_data.csv"]
    )

    _generate_test_submission(input_dir, output_dir)

    assert (output_dir / "simple.ipynb").exists()
    assert (output_dir / "gradebook.json").exists()

    output_dir2 = tmp_path / "output_dir2"
    output_dir2.mkdir()
    shutil.copyfile(output_dir / "gradebook.json", output_dir2 / "gradebook.json")

    _autograde_test_submission(str(output_dir), str(output_dir2))

    assert (output_dir2 / "simple.ipynb").exists()
    assert (output_dir2 / "gradebook.json").exists()

    output_dir3 = tmp_path / "output_dir3"
    output_dir3.mkdir()
    shutil.copyfile(output_dir2 / "gradebook.json", output_dir3 / "gradebook.json")

    GenerateFeedback(
        input_dir=str(output_dir2),
        output_dir=str(output_dir3),
        file_pattern="*.ipynb",
        config=None,
        assignment_settings=AssignmentSettings(),
    ).start()

    assert (output_dir3 / "simple.html").exists()
    assert (output_dir3 / "test.html").exists()
    assert not (output_dir3 / "assignment_data.csv").exists()


def test_generate_feedback_copy_with_all_files_allowed(tmp_path):
    input_dir, output_dir = _create_input_output_dirs(tmp_path, ["simple.ipynb"])

    _generate_test_submission(
        input_dir, output_dir, assignment_settings_kwargs={"allowed_files": ["*"]}
    )

    test_file = output_dir / "test.txt"
    test_file.touch()

    output_dir2 = tmp_path / "output_dir2"
    output_dir2.mkdir()
    shutil.copyfile(output_dir / "gradebook.json", output_dir2 / "gradebook.json")

    _autograde_test_submission(
        str(output_dir), str(output_dir2), assignment_settings_kwargs={"allowed_files": ["*"]}
    )

    output_dir3 = tmp_path / "output_dir3"
    output_dir3.mkdir()
    shutil.copyfile(output_dir2 / "gradebook.json", output_dir3 / "gradebook.json")

    GenerateFeedback(
        input_dir=str(output_dir2),
        output_dir=str(output_dir3),
        file_pattern="*.ipynb",
        config=None,
        assignment_settings=AssignmentSettings(allowed_files=["*"]),
    ).start()

    # Only the original notebook should be copied to the feedback
    assert (output_dir3 / "simple.html").exists()
    assert not (output_dir3 / "test.txt").exists()


def test_generate_feedback_with_student_notebooks(tmp_path):
    input_dir, output_dir = _create_input_output_dirs(tmp_path, ["simple.ipynb"])

    _generate_test_submission(
        input_dir, output_dir, assignment_settings_kwargs={"allowed_files": ["*.ipynb"]}
    )

    student_nb = output_dir / "student.ipynb"
    student_nb.touch()

    output_dir2 = tmp_path / "output_dir2"
    output_dir2.mkdir()
    shutil.copyfile(output_dir / "gradebook.json", output_dir2 / "gradebook.json")

    _autograde_test_submission(
        str(output_dir), str(output_dir2), assignment_settings_kwargs={"allowed_files": ["*.ipynb"]}
    )

    output_dir3 = tmp_path / "output_dir3"
    output_dir3.mkdir()
    shutil.copyfile(output_dir2 / "gradebook.json", output_dir3 / "gradebook.json")

    GenerateFeedback(
        input_dir=str(output_dir2),
        output_dir=str(output_dir3),
        file_pattern="*.ipynb",
        config=None,
        assignment_settings=AssignmentSettings(allowed_files=["*.ipynb"]),
    ).start()

    # Only the original notebook should be copied to the feedback
    assert (output_dir3 / "simple.html").exists()
    assert not (output_dir3 / "student.ipynb").exists()
    assert not (output_dir3 / "student.html").exists()


def test_generate_feedback_with_dirs(tmp_path):
    input_dir, output_dir = _create_input_output_dirs(tmp_path, ["simple.ipynb"])

    dir_1 = input_dir / "dir_1"
    dir_2 = dir_1 / "dir_2"
    dir_3 = dir_2 / "dir_3"
    dir_3.mkdir(parents=True)

    test_file = dir_3 / "test.txt"
    test_file.touch()

    _generate_test_submission(
        input_dir, output_dir, assignment_settings_kwargs={"allowed_files": ["*"]}
    )

    output_dir2 = tmp_path / "output_dir2"
    output_dir2.mkdir()
    shutil.copyfile(output_dir / "gradebook.json", output_dir2 / "gradebook.json")

    _autograde_test_submission(str(output_dir), str(output_dir2))

    assert (output_dir2 / "simple.ipynb").exists()
    assert (output_dir2 / "gradebook.json").exists()
    assert (output_dir2 / "dir_1").exists()
    assert (output_dir2 / "dir_1/dir_2").exists()
    assert (output_dir2 / "dir_1/dir_2/dir_3").exists()
    assert (output_dir2 / "dir_1/dir_2/dir_3/test.txt").exists()

    output_dir3 = tmp_path / "output_dir3"
    output_dir3.mkdir()
    shutil.copyfile(output_dir2 / "gradebook.json", output_dir3 / "gradebook.json")

    GenerateFeedback(
        input_dir=str(output_dir2),
        output_dir=str(output_dir3),
        file_pattern="*.ipynb",
        config=None,
        assignment_settings=AssignmentSettings(),
    ).start()

    assert (output_dir3 / "simple.html").exists()
    assert not (output_dir3 / "dir_1").exists()
    assert not (output_dir3 / "dir_1/dir_2").exists()
    assert not (output_dir3 / "dir_1/dir_2/dir_3").exists()
    assert not (output_dir3 / "dir_1/dir_2/dir_3/test.txt").exists()


def test_generate_feedback_with_missing_submission_file(tmp_path):
    """Test that GenerateFeedback handles files missing in the student submission gracefully"""
    input_dir, output_dir = _create_input_output_dirs(tmp_path, ["simple.ipynb"])

    _generate_test_submission(
        input_dir, output_dir, assignment_settings_kwargs={"allowed_files": ["*.ipynb"]}
    )

    # Student didn't submit the required notebook, but instead submitted a different one
    os.remove(output_dir / "simple.ipynb")
    student_nb = output_dir / "student.ipynb"
    student_nb.touch()

    output_dir2 = tmp_path / "output_dir2"
    output_dir2.mkdir()
    shutil.copyfile(output_dir / "gradebook.json", output_dir2 / "gradebook.json")

    _autograde_test_submission(
        str(output_dir), str(output_dir2), assignment_settings_kwargs={"allowed_files": ["*.ipynb"]}
    )

    output_dir3 = tmp_path / "output_dir3"
    output_dir3.mkdir()
    shutil.copyfile(output_dir2 / "gradebook.json", output_dir3 / "gradebook.json")

    gf = GenerateFeedback(
        input_dir=str(output_dir2),
        output_dir=str(output_dir3),
        file_pattern="*.ipynb",
        config=None,
        assignment_settings=AssignmentSettings(allowed_files=["*.ipynb"]),
    )
    gf.start()

    assert gf.notebooks == []
