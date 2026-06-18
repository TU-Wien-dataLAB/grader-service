import pathlib

import pytest


@pytest.fixture
def json_path(tmp_path: pathlib.Path):
    d = tmp_path / "out"
    d.mkdir()
    j = d / "gradebook.json"
    return str(j)
