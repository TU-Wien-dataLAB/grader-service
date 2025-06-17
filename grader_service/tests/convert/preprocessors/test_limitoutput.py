import pytest
import os

from grader_service.convert.preprocessors import LimitOutput
from .base import BaseTestPreprocessor


@pytest.fixture
def preprocessor():
    return LimitOutput()


class TestLimitOutput(BaseTestPreprocessor):
    def test_long_output(self):
        nb = self._read_nb(os.path.join("files", "long-output.ipynb"))
        (cell,) = nb.cells
        (output,) = cell.outputs
        assert len(output.text.split("\n")) > 1000

        pp = LimitOutput()
        nb, resources = pp.preprocess(nb, {})

        (cell,) = nb.cells
        (output,) = cell.outputs
        assert len(output.text.split("\n")) == 1000

    def test_infinite_recursion(self):
        nb = self._read_nb(os.path.join("files", "infinite-recursion.ipynb"))

        pp = LimitOutput()
        nb, resources = pp.preprocess(nb, {})

        (cell,) = nb.cells
        (output,) = cell.outputs
        assert len(output.traceback) == 100
