

import json
from typing import Tuple

from nbconvert.exporters.exporter import ResourcesDict
from nbformat.notebooknode import NotebookNode

from grader_convert.gradebook.gradebook import Gradebook, MissingEntry
from grader_convert.gradebook.models import GradeCell, SolutionCell, SourceCell, TaskCell
from grader_convert import utils
from grader_convert.preprocessors.base import NbGraderPreprocessor


class SaveCells(NbGraderPreprocessor):
    """A preprocessor to save information about grade and solution cells."""

    def _create_notebook(self, nb: NotebookNode) -> None:
        notebook_info = None

        try:
            notebook = self.gradebook.find_notebook(self.notebook_id)
        except MissingEntry:
            notebook_info = {}
        else:
            # pull out existing cell ids
            self.old_grade_cells = set(x.name for x in notebook.grade_cells)
            self.old_solution_cells = set(x.name for x in notebook.solution_cells)
            self.old_task_cells = set(x.name for x in notebook.task_cells)
            self.old_source_cells = set(x.name for x in notebook.source_cells)

            # clear data about the existing notebook
            self.log.debug(
                "Removing existing notebook '%s' from the database", self.notebook_id
            )
            notebook_info = notebook.to_dict()
            del notebook_info["name"]
            del notebook_info["grade_cells_dict"]
            del notebook_info["solution_cells_dict"]
            del notebook_info["task_cells_dict"]
            del notebook_info["source_cells_dict"]
            del notebook_info["grades_dict"]
            del notebook_info["comments_dict"]
            self.gradebook.remove_notebook(self.notebook_id)

        # create the notebook
        if notebook_info is not None:
            kernelspec = nb.metadata.get("kernelspec", {})
            notebook_info["kernelspec"] = json.dumps(kernelspec)
            notebook_info.setdefault("grade_cells_dict", dict())
            notebook_info.setdefault("solution_cells_dict", dict())
            notebook_info.setdefault("task_cells_dict", dict())
            notebook_info.setdefault("source_cells_dict", dict())
            notebook_info.setdefault("grades_dict", dict())
            notebook_info.setdefault("comments_dict", dict())
            notebook_info.setdefault("flagged", False)
            notebook_info["id"] = self.notebook_id
            self.log.debug("Creating notebook '%s' in the database", self.notebook_id)
            self.log.debug("Notebook kernelspec: {}".format(kernelspec))
            self.gradebook.add_notebook(self.notebook_id, **notebook_info)

        # save grade cells
        for name, info in self.new_grade_cells.items():
            grade_cell = self.gradebook.update_or_create_grade_cell(
                name, self.notebook_id, **info
            )
            self.log.debug("Recorded grade cell %s into the gradebook", grade_cell)

        # save solution cells
        for name, info in self.new_solution_cells.items():
            solution_cell = self.gradebook.update_or_create_solution_cell(
                name, self.notebook_id, **info
            )
            self.log.debug(
                "Recorded solution cell %s into the gradebook", solution_cell
            )

        # save task cells
        for name, info in self.new_task_cells.items():
            task_cell = self.gradebook.update_or_create_task_cell(
                name, self.notebook_id, **info
            )
            self.log.debug(
                "Recorded task cell %s into the gradebook from info %s", task_cell, info
            )

        # save source cells
        for name, info in self.new_source_cells.items():
            source_cell = self.gradebook.update_or_create_source_cell(
                name, self.notebook_id, **info
            )
            self.log.debug("Recorded source cell %s into the gradebook", source_cell)

    def preprocess(
        self, nb: NotebookNode, resources: ResourcesDict
    ) -> Tuple[NotebookNode, ResourcesDict]:
        # pull information from the resources
        self.notebook_id = resources["unique_key"]
        self.json_path = resources["output_json_path"]

        if self.notebook_id == "":
            raise ValueError("Invalid notebook id: '{}'".format(self.notebook_id))

        # create a place to put new cell information
        self.new_grade_cells = {}
        self.new_solution_cells = {}
        self.new_task_cells = {}
        self.new_source_cells = {}

        # connect to the database
        self.gradebook = Gradebook(self.json_path)

        with self.gradebook:
            nb, resources = super(SaveCells, self).preprocess(nb, resources)

            # create the notebook and save it to the database
            self._create_notebook(nb)

        return nb, resources

    def _create_grade_cell(self, cell: NotebookNode) -> None:
        grade_id = cell.metadata.nbgrader["grade_id"]

        try:
            grade_cell = self.gradebook.find_grade_cell(
                grade_id, self.notebook_id
            ).to_dict()
            del grade_cell["name"]
        except MissingEntry:
            grade_cell = GradeCell.empty_dict()
            del grade_cell["name"]

        grade_cell.update(
            {
                "max_score": float(cell.metadata.nbgrader["points"]),
                "cell_type": cell.cell_type,
            }
        )

        self.new_grade_cells[grade_id] = grade_cell

    def _create_solution_cell(self, cell: NotebookNode) -> None:
        grade_id = cell.metadata.nbgrader["grade_id"]

        try:
            solution_cell = self.gradebook.find_solution_cell(
                grade_id, self.notebook_id
            ).to_dict()
            del solution_cell["name"]
        except MissingEntry:
            solution_cell = SolutionCell.empty_dict()
            del solution_cell["name"]

        self.new_solution_cells[grade_id] = solution_cell

    def _create_task_cell(self, cell: NotebookNode) -> None:
        grade_id = cell.metadata.nbgrader["grade_id"]
        try:
            task_cell = self.gradebook.find_task_cell(
                grade_id, self.notebook_id
            ).to_dict()
            del task_cell["name"]
        except MissingEntry:
            task_cell = TaskCell.empty_dict()
            del task_cell["name"]

        task_cell.update(
            {
                "max_score": float(cell.metadata.nbgrader["points"]),
                "cell_type": cell.cell_type,
            }
        )

        self.new_task_cells[grade_id] = task_cell

    def _create_source_cell(self, cell: NotebookNode) -> None:
        grade_id = cell.metadata.nbgrader["grade_id"]

        try:
            source_cell = self.gradebook.find_source_cell(
                grade_id, self.notebook_id
            ).to_dict()
            del source_cell["name"]
        except MissingEntry:
            source_cell = SourceCell.empty_dict()
            del source_cell["name"]

        source_cell.update(
            {
                "cell_type": cell.cell_type,
                "locked": utils.is_locked(cell),
                "source": cell.source,
                "checksum": cell.metadata.nbgrader.get("checksum", None),
            }
        )

        self.new_source_cells[grade_id] = source_cell

    def preprocess_cell(
        self, cell: NotebookNode, resources: ResourcesDict, cell_index: int
    ) -> Tuple[NotebookNode, ResourcesDict]:

        if utils.is_grade(cell):
            self._create_grade_cell(cell)

        if utils.is_solution(cell):
            self._create_solution_cell(cell)

        if utils.is_task(cell):
            self._create_task_cell(cell)

        if (
            utils.is_grade(cell)
            or utils.is_solution(cell)
            or utils.is_locked(cell)
            or utils.is_task(cell)
        ):
            self._create_source_cell(cell)

        return cell, resources
