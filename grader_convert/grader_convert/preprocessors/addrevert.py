from typing import Dict, Tuple
from nbformat.notebooknode import NotebookNode
from grader_convert.preprocessors.base import NbGraderPreprocessor


class AddRevert(NbGraderPreprocessor):
    """Adds original code to cell which is used to revert the cell in extension"""

    def preprocess(
            self, nb: NotebookNode, resources: Dict
    ) -> Tuple[NotebookNode, Dict]:
        self.log.error("LOOOOOOOOOOOOOOOOOOGING")
        for cell in nb.cells:
            if cell.metadata["nbgrader"]["solution"]:
                cell.metadata["revert"] = cell.source
        return nb, resources
