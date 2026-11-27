import socket

from nbformat.v4 import new_code_cell, new_markdown_cell

from grader_service.convert.gradebook.models import CellType
from grader_service.convert.nbgraderformat import SCHEMA_VERSION


def create_code_cell():
    source = """print("something")
### BEGIN SOLUTION
print("hello")
### END SOLUTION"""
    cell = new_code_cell(source=source)
    return cell


def create_text_cell():
    source = "this is the answer!\n"
    cell = new_markdown_cell(source=source)
    return cell


def create_regular_cell(source, cell_type: CellType, schema_version=SCHEMA_VERSION):
    if cell_type == CellType.MARKDOWN:
        cell = new_markdown_cell(source=source)
    elif cell_type == CellType.CODE:
        cell = new_code_cell(source=source)
    else:
        raise ValueError(f"invalid cell type: {cell_type}")

    cell.metadata.nbgrader = {
        "grade": False,
        "grade_id": "",
        "points": 0.0,
        "solution": False,
        "task": False,
        "locked": False,
        "schema_version": schema_version,
    }

    return cell


def create_grade_cell(source, cell_type: CellType, grade_id, points, schema_version=SCHEMA_VERSION):
    if cell_type == CellType.MARKDOWN:
        cell = new_markdown_cell(source=source)
    elif cell_type == CellType.CODE:
        cell = new_code_cell(source=source)
    else:
        raise ValueError(f"invalid cell type: {cell_type}")

    cell.metadata.nbgrader = {
        "grade": True,
        "grade_id": grade_id,
        "points": points,
        "solution": False,
        "task": False,
        "locked": False,
        "schema_version": schema_version,
    }

    return cell


def create_solution_cell(source, cell_type: CellType, grade_id, schema_version=SCHEMA_VERSION):
    if cell_type == CellType.MARKDOWN:
        cell = new_markdown_cell(source=source)
    elif cell_type == CellType.CODE:
        cell = new_code_cell(source=source)
    else:
        raise ValueError(f"invalid cell type: {cell_type}")

    cell.metadata.nbgrader = {
        "solution": True,
        "grade_id": grade_id,
        "grade": False,
        "task": False,
        "locked": False,
        "schema_version": schema_version,
    }

    return cell


def create_locked_cell(source, cell_type: CellType, grade_id, schema_version=SCHEMA_VERSION):
    if cell_type == CellType.MARKDOWN:
        cell = new_markdown_cell(source=source)
    elif cell_type == CellType.CODE:
        cell = new_code_cell(source=source)
    else:
        raise ValueError(f"invalid cell type: {cell_type}")

    cell.metadata.nbgrader = {
        "locked": True,
        "grade_id": grade_id,
        "solution": False,
        "task": False,
        "grade": False,
        "schema_version": schema_version,
    }

    return cell


def create_grade_and_solution_cell(
    source, cell_type: CellType, grade_id, points, schema_version=SCHEMA_VERSION
):
    if cell_type == CellType.MARKDOWN:
        cell = new_markdown_cell(source=source)
    elif cell_type == CellType.CODE:
        cell = new_code_cell(source=source)
    else:
        raise ValueError(f"invalid cell type: {cell_type}")

    cell.metadata.nbgrader = {
        "solution": True,
        "grade": True,
        "task": False,
        "grade_id": grade_id,
        "points": points,
        "locked": False,
        "schema_version": schema_version,
    }

    return cell


def create_task_cell(source, cell_type: CellType, grade_id, points, schema_version=SCHEMA_VERSION):
    if cell_type == CellType.MARKDOWN:
        cell = new_markdown_cell(source=source)
    elif cell_type == CellType.CODE:
        cell = new_code_cell(source=source)
    else:
        raise ValueError(f"invalid cell type: {cell_type}")

    cell.metadata.nbgrader = {
        "solution": False,
        "grade": False,
        "task": True,
        "grade_id": grade_id,
        "points": points,
        "locked": True,
        "schema_version": schema_version,
    }

    return cell


def get_free_ports(n):
    """Based on https://gist.github.com/dbrgn/3979133"""
    ports = []
    sockets = []
    for i in range(n):
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        ports.append(port)
        sockets.append(s)
    for s in sockets:
        s.close()
    return ports
