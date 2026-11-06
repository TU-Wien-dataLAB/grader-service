from nbformat.notebooknode import NotebookNode

from grader_service.convert.preprocessors.base import NbGraderPreprocessor


class AddRevert(NbGraderPreprocessor):
    """Adds original code to cell which is used to revert the cell in
    extension"""

    def preprocess(self, nb: NotebookNode, resources: dict) -> tuple[NotebookNode, dict]:
        for cell in nb.cells:
            if "nbgrader" not in cell.metadata:
                cell.metadata["revert"] = cell.source
                continue

            if cell.metadata is None or cell.metadata["nbgrader"]["solution"]:
                cell.metadata["revert"] = cell.source

        return nb, resources
