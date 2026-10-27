import json

import pytest
from nbformat import validate
from nbformat.v4 import new_notebook

from grader_service.convert.gradebook.gradebook import Gradebook
from grader_service.convert.preprocessors import OverwriteKernelspec, SaveCells

from .base import BaseTestPreprocessor


@pytest.fixture
def preprocessors():
    return SaveCells(), OverwriteKernelspec()


class TestOverwriteKernelSpec(BaseTestPreprocessor):
    def test_overwrite_kernelspec(self, preprocessors, resources, gradebook: Gradebook):
        kernelspec = dict(display_name="blarg", name="python3", language="python")

        nb = new_notebook()
        nb.metadata["kernelspec"] = kernelspec
        nb, resources = preprocessors[0].preprocess(nb, resources)

        nb.metadata["kernelspec"] = {}
        nb, resources = preprocessors[1].preprocess(nb, resources)

        validate(nb)
        gradebook = Gradebook(dest_json=resources["output_json_path"])
        notebook = gradebook.find_notebook("test")
        assert nb.metadata["kernelspec"] == kernelspec
        assert json.loads(notebook.kernelspec) == kernelspec
