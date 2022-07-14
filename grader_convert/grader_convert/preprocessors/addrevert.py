from typing import Dict, Tuple
from nbformat.notebooknode import NotebookNode
from grader_convert.preprocessors.base import NbGraderPreprocessor


class AddRevert(NbGraderPreprocessor):
    """Adds original code to cell which is used to revert the cell in extension"""

    def preprocess(
            self, nb: NotebookNode, resources: Dict
    ) -> Tuple[NotebookNode, Dict]:
        for cell in nb.cells:

            if "nbgrader" not in cell.metadata:
                cell.metadata["revert"] = cell.source
                continue

            if cell.metadata is None or cell.metadata["nbgrader"]["solution"]:
                cell.metadata["revert"] = cell.source

        return nb, resources
