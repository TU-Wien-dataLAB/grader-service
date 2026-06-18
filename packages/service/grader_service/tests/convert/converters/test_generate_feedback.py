import json
import os

import pytest

from grader_service.api.models.assignment_settings import AssignmentSettings
from grader_service.convert.converters import GenerateFeedback
from grader_service.tests.convert.converters import _create_input_output_dirs


def _create_minimal_gradebook(nb_names: list | None = None):
    """Create a minimal valid gradebook structure.

    Note: Names in the notebook names list shouldn't contain file extension.
    """
    if nb_names is None:
        nb_names = ["simple", "test"]
    return {
        "notebooks": {
            name: {
                "id": f"{name}.ipynb",
                "name": f"{name}.ipynb",
                "kernelspec": "python3",
                "flagged": False,
                "grade_cells_dict": {},
                "solution_cells_dict": {},
                "task_cells_dict": {},
                "source_cells_dict": {},
                "grades_dict": {},
                "comments_dict": {},
                "_type": "Notebook",
            }
            for name in nb_names
        },
        "extra_files": [],
        "_type": "GradeBookModel",
    }


@pytest.mark.slow
def test_generate_feedback(tmp_path):
    input_dir, output_dir = _create_input_output_dirs(
        tmp_path, ["simple.ipynb", "test.ipynb", "assignment_data.csv"]
    )
    # Mock the slow autograding - just create a fake gradebook
    fake_gradebook = _create_minimal_gradebook(nb_names=["simple", "test"])
    (output_dir / "gradebook.json").write_text(json.dumps(fake_gradebook))

    GenerateFeedback(
        input_dir=str(input_dir),
        output_dir=str(output_dir),
        file_pattern="*.ipynb",
        config=None,
        assignment_settings=AssignmentSettings(),
    ).start()

    assert (output_dir / "simple.html").exists()
    assert (output_dir / "test.html").exists()
    assert not (output_dir / "assignment_data.csv").exists()


@pytest.mark.slow
def test_generate_feedback_copy_with_all_files_allowed(tmp_path):
    input_dir, output_dir = _create_input_output_dirs(tmp_path, ["simple.ipynb"])
    test_file = input_dir / "test.txt"
    test_file.touch()

    # Mock the slow autograding - just create a fake gradebook
    fake_gradebook = _create_minimal_gradebook(nb_names=["simple"])
    (output_dir / "gradebook.json").write_text(json.dumps(fake_gradebook))

    GenerateFeedback(
        input_dir=str(input_dir),
        output_dir=str(output_dir),
        file_pattern="*.ipynb",
        config=None,
        assignment_settings=AssignmentSettings(allowed_files=["*"]),
    ).start()

    # Only the original notebook should be copied to the feedback
    assert (output_dir / "simple.html").exists()
    assert not (output_dir / "test.txt").exists()


@pytest.mark.slow
def test_generate_feedback_with_student_notebooks(tmp_path):
    input_dir, output_dir = _create_input_output_dirs(tmp_path, ["simple.ipynb"])
    student_nb = input_dir / "student.ipynb"
    student_nb.touch()

    # Mock the slow autograding - just create a fake gradebook
    fake_gradebook = _create_minimal_gradebook(nb_names=["simple"])
    (output_dir / "gradebook.json").write_text(json.dumps(fake_gradebook))

    GenerateFeedback(
        input_dir=str(input_dir),
        output_dir=str(output_dir),
        file_pattern="*.ipynb",
        config=None,
        assignment_settings=AssignmentSettings(allowed_files=["*.ipynb"]),
    ).start()

    # Only the original notebook should be copied to the feedback
    assert (output_dir / "simple.html").exists()
    assert not (output_dir / "student.ipynb").exists()
    assert not (output_dir / "student.html").exists()


@pytest.mark.slow
def test_generate_feedback_with_dirs(tmp_path):
    input_dir, output_dir = _create_input_output_dirs(tmp_path, ["simple.ipynb"])

    dir_1 = input_dir / "dir_1"
    dir_2 = dir_1 / "dir_2"
    dir_3 = dir_2 / "dir_3"
    dir_3.mkdir(parents=True)

    test_file = dir_3 / "test.txt"
    test_file.touch()

    # Mock the slow autograding - just create a fake gradebook
    fake_gradebook = _create_minimal_gradebook(nb_names=["simple"])
    (output_dir / "gradebook.json").write_text(json.dumps(fake_gradebook))

    GenerateFeedback(
        input_dir=str(input_dir),
        output_dir=str(output_dir),
        file_pattern="*.ipynb",
        config=None,
        assignment_settings=AssignmentSettings(),
    ).start()

    assert (output_dir / "simple.html").exists()
    assert not (output_dir / "dir_1").exists()
    assert not (output_dir / "dir_1/dir_2").exists()
    assert not (output_dir / "dir_1/dir_2/dir_3").exists()
    assert not (output_dir / "dir_1/dir_2/dir_3/test.txt").exists()


def test_generate_feedback_with_missing_submission_file(tmp_path):
    """Test that GenerateFeedback handles files missing in the student submission gracefully"""
    input_dir, output_dir = _create_input_output_dirs(tmp_path, ["simple.ipynb"])

    # Student didn't submit the required notebook, but instead submitted a different one
    os.remove(input_dir / "simple.ipynb")
    student_nb = input_dir / "student.ipynb"
    student_nb.touch()

    # Mock the slow autograding - just create a fake gradebook
    fake_gradebook = _create_minimal_gradebook(nb_names=["simple"])
    (output_dir / "gradebook.json").write_text(json.dumps(fake_gradebook))

    gf = GenerateFeedback(
        input_dir=str(input_dir),
        output_dir=str(output_dir),
        file_pattern="*.ipynb",
        config=None,
        assignment_settings=AssignmentSettings(allowed_files=["*.ipynb"]),
    )
    gf.start()

    assert gf.notebooks == []
