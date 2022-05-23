

import json
import logging
import os
from functools import wraps
from typing import Any, Optional, Union

from nbconvert.exporters import notebook

from grader_convert.gradebook.models import (
    Comment,
    Grade,
    GradeBookModel,
    GradeCell,
    Notebook,
    SolutionCell,
    SourceCell,
    TaskCell,
)


class InvalidEntry(ValueError):
    pass


class MissingEntry(ValueError):
    pass


# TODO: add decorator to functions that sets dirty flag for methods and checks on __enter__
class Gradebook:
    """
    The gradebook object to interface with the JSON output file of a conversion.
    Should only be used as a context manager when changing the data.
    """

    def __init__(self, dest_json: str, log: logging.Logger = None) -> None:
        if log is None:
            from traitlets import log as l

            self.log = l.get_logger()
        else:
            self.log = log

        self.json_file: str = dest_json
        if os.path.isfile(self.json_file):
            with open(self.json_file, "r") as f:
                data = f.read()
                self.log.info(f"Reading {len(data)} bytes from {self.json_file}")
                self.data: dict = json.loads(data)
        else:
            os.makedirs(os.path.dirname(self.json_file), exist_ok=True)
            self.data: dict = {"notebooks": dict()}
            with open(self.json_file, "w") as f:
                json.dump(self.data, f)
        self.model: GradeBookModel = GradeBookModel.from_dict(self.data)

        self.in_context: int = 0
        self.dirty: bool = False

    def __enter__(self) -> "Gradebook":
        self.in_context += 1
        return self

    def __exit__(
        self,
        exc_type: Optional[Any],
        exc_value: Optional[Any],
        traceback: Optional[Any],
    ) -> None:
        self.in_context -= 1
        if self.dirty and exc_type is None:
            self.write_model()
            self.dirty = False

    @property
    def is_in_context(self) -> bool:
        return self.in_context > 0

    def write_model(self):
        """Writes JSON string to a JSON file"""
        with open(self.json_file, "w") as f:
            json_str = json.dumps(self.model.to_dict())
            self.log.info(
                f"Writing {len(json_str.encode('utf-8'))} bytes to {self.json_file}"
            )
            f.write(json_str)

    def write_access(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                self = args[0]
                if not isinstance(self, Gradebook):
                    raise RuntimeError(
                        "This decorator can only be used on methods inside Gradebook instances!"
                    )
            except IndexError:
                raise RuntimeError(
                    "This decorator can only be used on methods inside Gradebook instances!"
                )
            self.dirty = True
            result = fn(*args, **kwargs)
            if not self.is_in_context:
                self.write_model()
                self.dirty = False
            return result

        return wrapper

    # Notebooks
    @write_access
    def add_notebook(self, name: str, **kwargs: dict) -> Notebook:
        """
        Add a new notebook to the :class:`~GradeBookModel`.
        Parameters
        :param name:  the name of the new notebook
        :param kwargs: additional keyword arguments for the :class:`~Notebook` object
        :return: notebook : :class:`~Notebook`
        """
        kwargs = {
            k: v for k, v in kwargs.items() if k in set(Notebook.empty_dict().keys())
        }
        kwargs["name"] = name
        self.model.notebooks[name] = Notebook.from_dict(kwargs)

    def find_notebook(self, name: str) -> Notebook:
        """
        Find a particular notebook.
        :param name: the name of the notebook
        :return:  notebook : :class:`~Notebook`
        """
        try:
            return self.model.notebooks[name]
        except KeyError:
            raise MissingEntry()

    @write_access
    def update_or_create_notebook(self, name: str, **kwargs):
        """
        Update an existing notebook, or create it if it doesn't exist.
        :param name: the name of the notebook
        :param kwargs: additional keyword arguments for the :class:`~Notebook` object
        :return: notebook : :class:`~nNotebook`
        """
        raise NotImplementedError()

    @write_access
    def remove_notebook(self, name: str):
        """
        Deletes an existing notebook from the gradebook.
        :param name: the name of the notebook to delete
        :return: None
        """
        self.model.notebooks.pop(name, None)

    # Grade cells

    @write_access
    def add_grade_cell(self, name: str, notebook: str, **kwargs: dict) -> GradeCell:
        """
        Add a new grade cell to an existing notebook.
        :param name: the name of the new grade cell
        :param notebook: the name of an existing notebook
        :param kwargs: additional keyword arguments for :class:`~GradeCell`
        :return: grade_cell
        """
        kwargs = {
            k: v for k, v in kwargs.items() if k in set(GradeCell.empty_dict().keys())
        }
        kwargs["name"] = name
        nb = self.find_notebook(notebook)
        nb.grade_cells_dict[name] = GradeCell.from_dict(kwargs)
        return nb.grade_cells_dict[name]

    def find_grade_cell(self, name: str, notebook: str) -> GradeCell:
        """
        Find a grade cell in a particular notebook.
        :param name: the name of the grade cell
        :param notebook: the name of the notebook
        :return: grade_cell
        """
        nb = self.find_notebook(notebook)
        try:
            return nb.grade_cells_dict[name]
        except KeyError:
            raise MissingEntry()

    def find_graded_cell(self, name: str, notebook: str) -> Union[GradeCell, TaskCell]:
        """
        Find a graded cell in a particular notebook. This can be either a GradeCell or a TaskCell.
        :param name: the name of the grade cell
        :param notebook: the name of the notebook
        :return: grade_cell
        """
        nb = self.find_notebook(notebook)
        try:
            return [x for x in nb.graded_cells if x.name == name][0]
        except IndexError:
            raise MissingEntry()

    @write_access
    def update_or_create_grade_cell(
        self, name: str, notebook: str, **kwargs: dict
    ) -> GradeCell:
        """
        Update an existing grade cell in a notebook, or create the grade cell if it does not exist.
        :param name: the name of the grade cell
        :param notebook: the name of the notebook
        :param kwargs: additional keyword arguments for :class:`~GradeCell`
        :return: grade_cell
        """
        try:
            grade_cell = self.find_grade_cell(name, notebook)
        except MissingEntry:
            grade_cell = self.add_grade_cell(name, notebook, **kwargs)
        else:
            for attr in kwargs:
                setattr(grade_cell, attr, kwargs[attr])
        return grade_cell

    # Solution cells

    @write_access
    def add_solution_cell(
        self, name: str, notebook: str, **kwargs: dict
    ) -> SolutionCell:
        """
        Add a new solution cell to an existing notebook.
        :param name: the name of the new solution cell
        :param notebook: the name of an existing notebook
        :param kwargs: additional keyword arguments for :class:`~SolutionCell`
        :return: solution_cell : :class:`~SolutionCell`
        """
        kwargs = {
            k: v
            for k, v in kwargs.items()
            if k in set(SolutionCell.empty_dict().keys())
        }
        kwargs["name"] = name
        nb = self.find_notebook(notebook)
        nb.solution_cells_dict[name] = SolutionCell.from_dict(kwargs)
        return nb.solution_cells_dict[name]

    def find_solution_cell(self, name: str, notebook: str) -> SolutionCell:
        """
        Find a solution cell in a particular notebook.
        :param name: the name of the solution cell
        :param notebook: the name of the notebook
        :return: solution_cell : :class:`~SolutionCell`
        """
        nb = self.find_notebook(notebook)
        try:
            return nb.solution_cells_dict[name]
        except KeyError:
            raise MissingEntry()

    @write_access
    def update_or_create_solution_cell(
        self, name: str, notebook: str, **kwargs: dict
    ) -> SolutionCell:
        """
        Update an existing solution cell in a notebook, or create the solution cell if it does not exist.
        :param name: the name of the solution cell
        :param notebook: the name of the notebook
        :param kwargs: additional keyword arguments for :class:`~SolutionCell`
        :return: solution_cell
        """
        try:
            solution_cell = self.find_solution_cell(name, notebook)
        except MissingEntry:
            solution_cell = self.add_solution_cell(name, notebook, **kwargs)
        else:
            for attr in kwargs:
                setattr(solution_cell, attr, kwargs[attr])
        return solution_cell

    # Task cells

    @write_access
    def add_task_cell(self, name: str, notebook: str, **kwargs: dict) -> TaskCell:
        """
        Add a new task cell to an existing notebook.
        :param name: the name of the new task cell
        :param notebook: the name of an existing notebook
        :param kwargs: additional keyword arguments for :class:`~TaskCell`
        :return: task_cell
        """
        kwargs = {
            k: v for k, v in kwargs.items() if k in set(TaskCell.empty_dict().keys())
        }
        kwargs["name"] = name
        nb = self.find_notebook(notebook)
        nb.task_cells_dict[name] = TaskCell.from_dict(kwargs)
        return nb.task_cells_dict[name]

    def find_task_cell(self, name: str, notebook: str) -> TaskCell:
        """
        Find a task cell in a particular notebook.
        :param name: the name of the task cell
        :param notebook: the name of the notebook
        :return: task_cell : :class:`~TaskCell`
        """
        nb = self.find_notebook(notebook)
        try:
            return nb.task_cells_dict[name]
        except KeyError:
            raise MissingEntry()

    @write_access
    def update_or_create_task_cell(
        self, name: str, notebook: str, **kwargs
    ) -> TaskCell:
        """
        Update an existing task cell in a notebook, or create the task cell if it does not exist.
        :param name: the name of the task cell
        :param notebook: the name of the notebook
        :param kwargs: additional keyword arguments for :class:`~TaskCell`
        :return: task_cell : :class:`~TaskCell`
        """
        try:
            task_cell = self.find_task_cell(name, notebook)
        except MissingEntry:
            task_cell = self.add_task_cell(name, notebook, **kwargs)
        else:
            for attr in kwargs:
                setattr(task_cell, attr, kwargs[attr])
        return task_cell

    # Source cell

    @write_access
    def add_source_cell(self, name: str, notebook: str, **kwargs: dict) -> SourceCell:
        """
        Add a new source cell to an existing notebook.
        :param name: the name of the new source cell
        :param notebook: the name of an existing notebook
        :param kwargs: additional keyword arguments for :class:`~SourceCell`
        :return: source_cell : :class:`~SourceCell`
        """
        kwargs = {
            k: v for k, v in kwargs.items() if k in set(SourceCell.empty_dict().keys())
        }
        kwargs["name"] = name
        nb = self.find_notebook(notebook)
        nb.source_cells_dict[name] = SourceCell.from_dict(kwargs)
        return nb.source_cells_dict[name]

    def find_source_cell(self, name: str, notebook: str) -> SourceCell:
        """
        Find a source cell in a particular notebook.
        :param name: the name of the source cell
        :param notebook: the name of the notebook
        :return: source_cell : :class:`~SourceCell`
        """
        nb = self.find_notebook(notebook)
        try:
            return nb.source_cells_dict[name]
        except KeyError:
            raise MissingEntry()

    @write_access
    def update_or_create_source_cell(
        self, name: str, notebook: str, **kwargs: dict
    ) -> SourceCell:
        """
        Update an existing source cell in a notebook of an assignment, or
        create the source cell if it does not exist.
        :param name: the name of the source cell
        :param notebook: the name of the notebook
        :param kwargs: additional keyword arguments for :class:`~SourceCell`
        :return: source_cell
        """
        try:
            source_cell = self.find_source_cell(name, notebook)
        except MissingEntry:
            source_cell = self.add_source_cell(name, notebook, **kwargs)
        else:
            for attr in kwargs:
                setattr(source_cell, attr, kwargs[attr])
        return source_cell

    # Grades

    @write_access
    def add_grade(self, grade_cell: str, notebook: str, grade: Grade) -> Grade:
        """
        Add a grade to a notebook.
        :param grade_cell: the name of a grade or task cell
        :param notebook: the name of a notebook
        :param grade: the grade to add
        :return: grade
        """
        nb = self.find_notebook(notebook)

        grade_c: GradeCell = nb.grade_cells_dict.get(grade_cell, None)
        task_c: TaskCell = nb.task_cells_dict.get(grade_cell, None)
        solution_c: SolutionCell = nb.solution_cells_dict.get(grade_cell, None)
        if all([x is None for x in [grade_c, task_c, solution_c]]):
            raise MissingEntry()
        grade.id = grade_cell
        grade.notebook_id = notebook
        grade.cell_id = grade_cell
        if grade_c is not None:
            grade.max_score_gradecell = grade_c.max_score
            grade_c.grade_id = grade.id
        if task_c is not None:
            grade.max_score_taskcell = task_c.max_score
            task_c.grade_id = grade.id
        if solution_c is not None:
            solution_c.grade_id = grade.id
        nb.grades_dict[grade.id] = grade
        return grade

    def find_grade(self, grade_cell: str, notebook: str) -> Grade:
        """
        Find a particular grade in a notebook.
        If the grade does not exists an empty grade object is returned.
        :param grade_cell: the name of a grade or task cell
        :param notebook: the name of a notebook
        :return: grade
        """
        nb = self.find_notebook(notebook)
        try:
            return nb.grades_dict[grade_cell]
        except KeyError:
            return Grade.from_dict(Grade.empty_dict())

    @write_access
    def add_comment(
        self, solution_cell: str, notebook: str, comment: Comment
    ) -> Comment:
        """
        Add a comment to a notebook.
        :param solution_cell: the name of a solution or task cell
        :param notebook: the name of a notebook
        :param comment: the comment to add
        :return: comment
        """
        nb = self.find_notebook(notebook)

        grade_c: GradeCell = nb.grade_cells_dict.get(solution_cell, None)
        task_c: TaskCell = nb.task_cells_dict.get(solution_cell, None)
        solution_c: SolutionCell = nb.solution_cells_dict.get(solution_cell, None)
        if all([x is None for x in [solution_c, task_c, solution_c]]):
            raise MissingEntry()
        comment.id = solution_cell
        comment.notebook_id = notebook
        comment.cell_id = solution_cell
        if grade_c is not None:
            grade_c.comment_id = comment.id
        if task_c is not None:
            task_c.comment_id = comment.id
        if solution_c is not None:
            solution_c.comment_id = comment.id
        nb.comments_dict[comment.id] = comment
        return comment

    def find_comment(self, solution_cell: str, notebook: str) -> Comment:
        """
        Find a particular comment in a notebook.
        :param solution_cell: the name of a solution or task cell
        :param notebook: the name of a notebook
        :return: comment
        """
        nb = self.find_notebook(notebook)
        try:
            return nb.comments_dict[solution_cell]
        except KeyError:
            return Comment.from_dict(Comment.empty_dict())
