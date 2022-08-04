from . import _create_input_output_dirs
from converters import GenerateAssignment


def test_generate_assignment(tmp_path):
    input_dir, output_dir = _create_input_output_dirs(tmp_path, ["simple.ipynb"])

    GenerateAssignment(
        input_dir=str(input_dir),
        output_dir=str(output_dir),
        file_pattern="*.ipynb",
        copy_files=False,
        config=None
    ).start()

    assert (output_dir / "simple.ipynb").exists()
    assert (output_dir / "gradebook.json").exists()


def test_generate_assignment_no_copy_with_files(tmp_path):
    input_dir, output_dir = _create_input_output_dirs(tmp_path, ["simple.ipynb"])
    test_file = input_dir / "test.txt"
    test_file.touch()
    assert test_file.exists()

    GenerateAssignment(
        input_dir=str(input_dir),
        output_dir=str(output_dir),
        file_pattern="*.ipynb",
        copy_files=False,
        config=None
    ).start()

    assert (output_dir / "simple.ipynb").exists()
    assert (output_dir / "gradebook.json").exists()
    assert not (output_dir / "test.txt").exists()


def test_generate_assignment_copy_with_files(tmp_path):
    input_dir, output_dir = _create_input_output_dirs(tmp_path, ["simple.ipynb"])
    test_file = input_dir / "test.txt"
    test_file.touch()
    assert test_file.exists()

    GenerateAssignment(
        input_dir=str(input_dir),
        output_dir=str(output_dir),
        file_pattern="*.ipynb",
        copy_files=True,
        config=None
    ).start()

    assert (output_dir / "simple.ipynb").exists()
    assert (output_dir / "gradebook.json").exists()
    assert (output_dir / "test.txt").exists()


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
        copy_files=True,
        config=None
    ).start()

    assert (output_dir / "simple.ipynb").exists()
    assert (output_dir / "gradebook.json").exists()
    assert (output_dir / "dir_1").exists()
    assert (output_dir / "dir_1/dir_2").exists()
    assert (output_dir / "dir_1/dir_2/dir_3").exists()
    assert (output_dir / "dir_1/dir_2/dir_3/test.txt").exists()
