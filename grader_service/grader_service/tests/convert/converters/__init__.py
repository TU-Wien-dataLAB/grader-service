import shutil
from pathlib import Path

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
