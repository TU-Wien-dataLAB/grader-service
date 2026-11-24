from pathlib import Path


def create_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def remove_file(path: Path):
    path.unlink()
