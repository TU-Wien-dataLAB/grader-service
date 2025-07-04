import shutil
from pathlib import Path
from typing import Any, Dict

from grader_service.api.models.assignment_settings import AssignmentSettings
from grader_service.convert.converters import GenerateAssignment

tests_dir = Path(__file__).parent.parent


def _create_input_output_dirs(p: Path, input_notebooks=None):
    input_dir = p / "input"
    output_dir = p / "output"
    input_dir.mkdir()
    output_dir.mkdir()

    if input_notebooks:
        for n in input_notebooks:
            shutil.copyfile(tests_dir / f"preprocessors/files/{n}", input_dir / n)

    return input_dir, output_dir


def _generate_test_assignment(
    input_dir: str,
    output_dir: str,
    file_pattern: str = "*.ipynb",
    assignment_settings_kwargs: Dict[str, Any] = None,
):
    if assignment_settings_kwargs is None:
        assignment_settings_kwargs = {}

    GenerateAssignment(
        input_dir=input_dir,
        output_dir=output_dir,
        file_pattern=file_pattern,
        assignment_settings=AssignmentSettings(**assignment_settings_kwargs),
        config=None,
    ).start()
