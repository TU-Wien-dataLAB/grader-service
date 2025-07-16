from typing import Tuple

from nbconvert.exporters.exporter import ResourcesDict
from nbformat.notebooknode import NotebookNode

from grader_service.convert import utils
from grader_service.convert.preprocessors.base import NbGraderPreprocessor


class DeduplicateIds(NbGraderPreprocessor):
    """A preprocessor to overwrite information about grade and solution cells."""

    def preprocess(
        self, nb: NotebookNode, resources: ResourcesDict
    ) -> Tuple[NotebookNode, ResourcesDict]:
        # keep track of grade ids encountered so far
        self.grade_ids = set([])

        # process each cell in reverse order
        nb, resources = super(DeduplicateIds, self).preprocess(nb, resources)

        return nb, resources

    def preprocess_cell(
        self, cell: NotebookNode, resources: ResourcesDict, cell_index: int
    ) -> Tuple[NotebookNode, ResourcesDict]:
        if not (utils.is_grade(cell) or utils.is_solution(cell) or utils.is_locked(cell)):
            self.log.warning("cell above")
            return cell, resources

        grade_id = cell.metadata.nbgrader["grade_id"]

        if grade_id in self.grade_ids:
            self.log.warning("Cell with id '%s' exists multiple times!", grade_id)
            cell.metadata = {}
        else:
            self.grade_ids.add(grade_id)

        return cell, resources
