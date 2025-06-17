import os
from .base import BaseTestPreprocessor
from grader_service.convert.preprocessors import Execute
from nbconvert.preprocessors import ExecutePreprocessor
from nbconvert.exporters.exporter import ResourcesDict


class TestExecute(BaseTestPreprocessor):
    def test_simple_execute_nbconvert(self):
        nb = self._read_nb(os.path.join("files", "simple.ipynb"))
        pp = ExecutePreprocessor(timeout=60, kernel_name="python3")

        nb, resources = pp.preprocess(nb, {})
        assert nb is not None
        assert resources is not None

    def test_simple_execute_convert(self):
        nb = self._read_nb(os.path.join("files", "simple.ipynb"))
        pp = Execute(timeout=5, kernel_name="python3", interrupt_on_timeout=False)
        # pp.interrupt_on_timeout = False

        res = ResourcesDict()
        nb, resources = pp.preprocess(nb, res)
        assert nb is not None
        assert resources is not None
