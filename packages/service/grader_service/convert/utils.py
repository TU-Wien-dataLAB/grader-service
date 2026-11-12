import contextlib
import hashlib
import json
import os
from collections.abc import Iterator
from logging import Logger
from typing import Any

from nbformat.notebooknode import NotebookNode

from grader_service.api.models.assignment_settings import AssignmentSettings
from grader_service.convert.gradebook.models import CellType


def get_assignment_settings_from_env() -> AssignmentSettings:
    """Read env var and returns assignment settings

    Returns:
        AssignmentSettings: assignment settings
    """
    settings_json_str = os.getenv("ASSIGNMENT_SETTINGS", "{}")
    settings_dict = json.loads(settings_json_str)
    return AssignmentSettings.from_dict(settings_dict)


def is_task(cell: NotebookNode) -> bool:
    """Returns True if the cell is a task cell."""
    if "nbgrader" not in cell.metadata:
        return False
    return cell.metadata["nbgrader"].get("task", False)


def is_grade(cell: NotebookNode) -> bool:
    """Returns True if the cell is a grade cell."""
    if "nbgrader" not in cell.metadata:
        return False
    return cell.metadata["nbgrader"].get("grade", False)


def has_cell_type(cell: NotebookNode) -> bool:
    """Returns True if the cell has a cell type."""
    if not grade_id_present(cell):
        return False

    # validate cell metadata
    grade = cell.metadata["nbgrader"]["grade"]
    solution = cell.metadata["nbgrader"]["solution"]
    locked = cell.metadata["nbgrader"]["locked"]
    grade_id = cell.metadata["nbgrader"]["grade_id"]

    return any([grade, solution, locked, grade_id])


def is_solution(cell: NotebookNode) -> bool:
    """Returns True if the cell is a solution cell."""
    if "nbgrader" not in cell.metadata:
        return False
    return cell.metadata["nbgrader"].get("solution", False)


def is_locked(cell: NotebookNode) -> bool:
    """Returns True if the cell source is locked (will be overwritten)."""
    if "nbgrader" not in cell.metadata or is_solution(cell):
        return False
    elif is_grade(cell):
        return True
    else:
        return cell.metadata["nbgrader"].get("locked", False)


def get_partial_grade(output, max_points, log=None):
    """
    Calculates partial grade for a cell, based on contents of
    output["data"]["text/plain"]. Returns a value between 0
    and max_points. Returns max_points (and a warning) for edge cases.
    """
    # check that output["data"]["text/plain"] exists
    if not output["data"]["text/plain"]:
        raise KeyError("output ['data']['text/plain'] does not exist")
    grade = output["data"]["text/plain"]
    # For partial credit, expecting grade to be a value between 0
    # and max_points
    # A valid value for key output["data"]["text/plain"] can be a
    # list or a string, so handle the string case
    if isinstance(grade, list):
        # grade is a list
        if len(grade) > 1:
            if log:
                warning_msg = f"""Cell output is {grade}, which is a list. For autograder tests,
                the output is expected to indicate partial credit and be a single value between 0.0
                and max_points. Currently treating other output as full credit, but future releases
                may treat it as error."""
                log.warning(warning_msg)
            return max_points
        # if a single value in list, set grade to that value
        grade = grade[0]
    try:
        # now that we have a single values for grade, can we convert to a float?
        grade = float(grade)
    except ValueError:
        if log:
            warning_msg = f"""Cell output is {grade}, which cannot be converted to a float. For
            autograder tests, the output is expected to indicate partial credit and be single value
            between 0.0 and max_points. Currently treating other output as full credit, but future
            releases may treat it as error."""
            log.warning(warning_msg)
        return max_points
    if grade >= 0.0:
        if grade > max_points:
            raise ValueError("partial credit cannot be greater than maximum points for cell")
        return grade
    else:
        if log:
            warning_msg = f"""Cell output is {grade}, which is less than 0.0.
            This is strange."""
            log.warning(warning_msg)
        return max_points


def determine_grade(cell: NotebookNode, log: Logger | None = None) -> tuple[float | None, float]:
    if not is_grade(cell):
        raise ValueError("cell is not a grade cell")

    max_points = float(cell.metadata["nbgrader"]["points"])
    if is_solution(cell):
        # if it's a solution cell and the checksum hasn't changed, that means
        # they didn't provide a response, so we can automatically give this a
        # zero grade
        if "checksum" in cell.metadata.nbgrader and cell.metadata.nbgrader[
            "checksum"
        ] == compute_checksum(cell):
            return 0, max_points
        else:
            return None, max_points

    elif cell.cell_type == CellType.CODE:
        # for code cells, we look at the output. There are three options:
        # 1. output contains an error (no credit);
        # 2. output is a value greater than 0 (partial credit);
        # 3. output is something else, or nothing (full credit).
        for output in cell.outputs:
            # option 1: error, return 0
            if (
                output.output_type == "error"
                or output.output_type == "stream"
                and output.name == "stderr"
            ):
                return 0, max_points
            # if not error, then check for option 2, partial credit
            if output.output_type == "execute_result":
                # is there a single result that can be cast to a float?
                partial_grade = get_partial_grade(output, max_points, log)
                return partial_grade, max_points

        # otherwise, assume all fine and return all the points
        return max_points, max_points

    else:
        return None, max_points


def to_bytes(string: str) -> bytes:
    """A helper function for converting a string to bytes with utf-8 encoding."""
    return bytes(string.encode("utf-8"))


def compute_checksum(cell: NotebookNode) -> str:
    m = hashlib.md5()
    # add the cell source and type
    m.update(to_bytes(cell.source))
    m.update(to_bytes(cell.cell_type))

    # add whether it's a grade cell and/or solution cell
    m.update(to_bytes(str(is_grade(cell))))
    m.update(to_bytes(str(is_solution(cell))))
    m.update(to_bytes(str(is_locked(cell))))

    # include the cell id
    m.update(to_bytes(cell.metadata.nbgrader["grade_id"]))

    # include the number of points that the cell is worth, if it is a grade cell
    if is_grade(cell):
        m.update(to_bytes(str(float(cell.metadata.nbgrader["points"]))))

    return m.hexdigest()


@contextlib.contextmanager
def chdir(dirname: str) -> Iterator:
    currdir = os.getcwd()
    if dirname:
        os.chdir(dirname)
    try:
        yield
    finally:
        os.chdir(currdir)


@contextlib.contextmanager
def setenv(**kwargs: Any) -> Iterator:
    previous_env = {}
    for key, value in kwargs.items():
        previous_env[key] = os.environ.get(value)
        os.environ[key] = value
    yield
    for key, value in kwargs.items():
        if previous_env[key] is None:
            del os.environ[key]
        else:
            os.environ[key] = previous_env[key]


def grade_id_present(cell):
    return cell.metadata.get("nbgrader", {}).get("grade_id") is not None
