

import typing as t
from textwrap import dedent
from typing import Any, Optional, Tuple

from jupyter_client.utils import ensure_async, run_sync
from nbclient import NotebookClient
from nbclient.exceptions import CellTimeoutError
from nbconvert.exporters.exporter import ResourcesDict
from nbconvert.preprocessors import CellExecutionError, ExecutePreprocessor
from nbformat.notebooknode import NotebookNode
from traitlets import Bool, Integer, List

from grader_convert.preprocessors.base import NbGraderPreprocessor


class UnresponsiveKernelError(Exception):
    pass


class Execute(NbGraderPreprocessor, ExecutePreprocessor):
    interrupt_on_timeout = Bool(True)
    allow_errors = Bool(True)
    raise_on_iopub_timeout = Bool(True)
    extra_arguments = List(
        [],
        help=dedent(
            """
        A list of extra arguments to pass to the kernel. For python kernels,
        this defaults to ``--HistoryManager.hist_file=:memory:``. For other
        kernels this is just an empty list.
        """
        ),
    ).tag(config=True)

    execute_retries = Integer(
        0,
        help=dedent(
            """
        The number of times to try re-executing the notebook before throwing
        an error. Generally, this shouldn't need to be set, but might be useful
        for CI environments when tests are flaky.
        """
        ),
    ).tag(config=True)

    def preprocess(
            self, nb: NotebookNode, resources: ResourcesDict, retries: Optional[Any] = None
    ) -> Tuple[NotebookNode, ResourcesDict]:
        # This gets added in by the parent execute preprocessor, so if it's already in our
        # extra arguments we need to delete it or traitlets will be unhappy.
        if "--HistoryManager.hist_file=:memory:" in self.extra_arguments:
            self.extra_arguments.remove("--HistoryManager.hist_file=:memory:")

        if retries is None:
            retries = self.execute_retries
        try:
            output = super(Execute, self).preprocess(nb, resources)
        except RuntimeError:
            if retries == 0:
                raise UnresponsiveKernelError()
            else:
                self.log.warning("Failed to execute notebook, trying again...")
                return self.preprocess(nb, resources, retries=retries - 1)

        return output

    async def _async_handle_timeout(self, timeout: int, cell: t.Optional[NotebookNode] = None) -> None:
        await super()._async_handle_timeout(timeout, cell)

        error_output = NotebookNode(output_type="error")
        error_output.ename = "CellTimeoutError"
        error_output.evalue = "CellTimeoutError"
        error_output.traceback = [
            f"CellTimeoutInterrupt: Cell execution timed out after maximum execution time of {self.timeout} seconds."]
        cell.outputs.append(error_output)
