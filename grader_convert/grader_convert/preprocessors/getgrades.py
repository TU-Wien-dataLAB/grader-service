

from typing import Tuple

from nbconvert.exporters.exporter import ResourcesDict
from nbformat.notebooknode import NotebookNode
from traitlets import List

from grader_convert.gradebook.gradebook import Gradebook
from grader_convert import utils
from grader_convert.preprocessors.base import NbGraderPreprocessor

class GetGrades(NbGraderPreprocessor):
    """Preprocessor for saving grades from the database to the notebook"""

    display_data_priority = List(
        [
            "text/html",
            "application/pdf",
            "text/latex",
            "image/svg+xml",
            "image/png",
            "image/jpeg",
            "text/plain",
        ],
        config=True,
    )

    def preprocess(
        self,
        nb: NotebookNode,
        resources: ResourcesDict,
    ) -> Tuple[NotebookNode, ResourcesDict]:
        # pull information from the resources
        self.notebook_id = resources["unique_key"]
        self.json_path = resources["output_json_path"]

        # connect to the database
        self.gradebook = Gradebook(self.json_path)

        with self.gradebook:
            # process the cells
            nb, resources = super(GetGrades, self).preprocess(nb, resources)
            notebook = self.gradebook.find_notebook(self.notebook_id)

            resources["nbgrader"]["score"] = notebook.score
            resources["nbgrader"]["max_score"] = notebook.max_score

        return nb, resources

    def _get_comment(self, cell: NotebookNode, resources: ResourcesDict) -> None:
        """Graders can optionally add comments to the student's solutions, so
        add the comment information into the database if it doesn't
        already exist. It should NOT overwrite existing comments that
        might have been added by a grader already.

        """

        # retrieve or create the comment object from the database
        comment = self.gradebook.find_comment(
            cell.metadata["nbgrader"]["grade_id"], self.notebook_id
        )

        # save it in the notebook
        cell.metadata.nbgrader["comment"] = comment.comment

    def _get_score(self, cell: NotebookNode, resources: ResourcesDict) -> None:
        grade = self.gradebook.find_grade(
            cell.metadata["nbgrader"]["grade_id"], self.notebook_id
        )

        cell.metadata.nbgrader["score"] = grade.score
        cell.metadata.nbgrader["points"] = grade.max_score

    def preprocess_cell(
        self,
        cell: NotebookNode,
        resources: ResourcesDict,
        cell_index: int,
    ) -> Tuple[NotebookNode, ResourcesDict]:
        # if it's a solution cell, then add a comment
        if utils.is_solution(cell):
            self._get_comment(cell, resources)

        # if it's a grade cell, the add a grade
        if utils.is_grade(cell):
            self._get_score(cell, resources)
        # if it's a task cell, then add a comment and a score
        if utils.is_task(cell):
            self._get_comment(cell, resources)
            self._get_score(cell, resources)

        return cell, resources
