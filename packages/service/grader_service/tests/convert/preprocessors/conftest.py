import os
import pathlib

import pytest
from nbconvert.exporters import ResourcesDict

from grader_service.convert.gradebook.gradebook import Gradebook


@pytest.fixture
def json_path(tmp_path: pathlib.Path):
    d = tmp_path / "out"
    d.mkdir()
    j = d / "gradebook.json"
    return str(j)


@pytest.fixture
def gradebook(request, json_path):
    gb = Gradebook(json_path)

    def fin():
        os.remove(json_path)

    request.addfinalizer(fin)

    return gb


@pytest.fixture
def resources(json_path):
    return ResourcesDict(
        unique_key="test",
        output_json_file="gradebook.json",
        output_json_path=json_path,
        nbgrader=dict(),
    )
