import os
import shutil
import tempfile

import pytest
from nbformat.v4 import new_output

from grader_service.convert import utils
from grader_service.convert.gradebook.models import CellType

from .. import (
    create_code_cell,
    create_grade_and_solution_cell,
    create_grade_cell,
    create_solution_cell,
)


@pytest.fixture
def temp_cwd(request):
    orig_dir = os.getcwd()
    path = tempfile.mkdtemp()
    os.chdir(path)

    def fin():
        os.chdir(orig_dir)
        shutil.rmtree(path)

    request.addfinalizer(fin)

    return path


def test_is_grade():
    cell = create_code_cell()
    assert not utils.is_grade(cell)
    cell.metadata["nbgrader"] = {}
    assert not utils.is_grade(cell)
    cell.metadata["nbgrader"]["grade"] = False
    assert not utils.is_grade(cell)
    cell.metadata["nbgrader"]["grade"] = True
    assert utils.is_grade(cell)


def test_is_solution():
    cell = create_code_cell()
    assert not utils.is_solution(cell)
    cell.metadata["nbgrader"] = {}
    assert not utils.is_solution(cell)
    cell.metadata["nbgrader"]["solution"] = False
    assert not utils.is_solution(cell)
    cell.metadata["nbgrader"]["solution"] = True
    assert utils.is_solution(cell)


def test_is_locked():
    cell = create_code_cell()
    assert not utils.is_locked(cell)
    cell.metadata["nbgrader"] = {"solution": True, "grade": False, "locked": False}
    assert not utils.is_locked(cell)

    cell = create_code_cell()
    assert not utils.is_locked(cell)
    cell.metadata["nbgrader"] = {"solution": True, "grade": True, "locked": False}
    assert not utils.is_locked(cell)

    cell = create_code_cell()
    assert not utils.is_locked(cell)
    cell.metadata["nbgrader"] = {"solution": True, "grade": False, "locked": True}
    assert not utils.is_locked(cell)

    cell = create_code_cell()
    assert not utils.is_locked(cell)
    cell.metadata["nbgrader"] = {"solution": True, "grade": True, "locked": True}
    assert not utils.is_locked(cell)

    cell = create_code_cell()
    assert not utils.is_locked(cell)
    cell.metadata["nbgrader"] = {"solution": False, "grade": True, "locked": False}
    assert utils.is_locked(cell)

    cell = create_code_cell()
    assert not utils.is_locked(cell)
    cell.metadata["nbgrader"] = {"solution": False, "grade": True, "locked": True}
    assert utils.is_locked(cell)

    cell = create_code_cell()
    assert not utils.is_locked(cell)
    cell.metadata["nbgrader"] = {"solution": False, "grade": False, "locked": True}
    assert utils.is_locked(cell)

    assert utils.is_locked(cell)
    cell = create_code_cell()
    assert not utils.is_locked(cell)
    cell.metadata["nbgrader"] = {"solution": False, "grade": False, "locked": False}
    assert not utils.is_locked(cell)


def test_determine_grade_code_grade():
    cell = create_grade_cell('print("test")', CellType.CODE, "foo", 10)
    cell.outputs = []
    assert utils.determine_grade(cell) == (10, 10)

    cell.outputs = [
        new_output("error", ename="NotImplementedError", evalue="", traceback=["error"])
    ]
    assert utils.determine_grade(cell) == (0, 10)


def test_determine_grade_markdown_grade():
    cell = create_grade_cell("test", CellType.MARKDOWN, "foo", 10)
    assert utils.determine_grade(cell) == (None, 10)


def test_determine_grade_solution():
    cell = create_solution_cell("test", CellType.CODE, "foo")
    with pytest.raises(ValueError):
        utils.determine_grade(cell)

    cell = create_solution_cell("test", CellType.MARKDOWN, "foo")
    with pytest.raises(ValueError):
        utils.determine_grade(cell)


def test_determine_grade_code_grade_and_solution():
    cell = create_grade_and_solution_cell("test", CellType.CODE, "foo", 10)
    cell.metadata.nbgrader["checksum"] = utils.compute_checksum(cell)
    cell.outputs = []
    assert utils.determine_grade(cell) == (0, 10)

    cell.outputs = [
        new_output("error", ename="NotImplementedError", evalue="", traceback=["error"])
    ]
    cell.source = "test!"
    assert utils.determine_grade(cell) == (None, 10)


def test_get_partial_grade():
    # test single value in list
    test_data = {"data": {"text/plain": ["0.6"]}}
    assert utils.get_partial_grade(test_data, 1.0) == 0.6

    # test single value not in list
    test_data = {"data": {"text/plain": "6.0"}}
    assert utils.get_partial_grade(test_data, 10.0) == 6.0

    # test zero
    test_data = {"data": {"text/plain": ["0.0"]}}
    assert utils.get_partial_grade(test_data, 1.0) == 0.0

    # test string in list, should assume partial credit not intended
    test_data = {"data": {"text/plain": ["'this is a string'"]}}
    assert utils.get_partial_grade(test_data, 2.0) == 2.0

    # test returning too many points
    test_data = {"data": {"text/plain": ["2.0"]}}
    with pytest.raises(ValueError):
        utils.get_partial_grade(test_data, 1.0)

    test_data = {"fake_key": 4}
    with pytest.raises(KeyError):
        utils.get_partial_grade(test_data, 2.0)


def test_determine_grade_code_partial_credit():
    # create grade cell with max_points == 5
    cell = create_grade_cell("test", CellType.CODE, "foo", 5)

    # simple case when output between 0 and max_points
    test_data = {"text/plain": "3"}
    cell.outputs = [new_output(output_type="execute_result", execution_count=1, data=test_data)]
    assert utils.determine_grade(cell) == (3, 5)

    # should give error when partial_credit > max_grade
    cell.outputs = []
    test_data = {"text/plain": "5.5"}
    cell.outputs = [new_output(output_type="execute_result", execution_count=1, data=test_data)]
    with pytest.raises(ValueError):
        utils.determine_grade(cell)

    # returns max_points if output is a list
    cell.outputs = []
    test_data = {"text/plain": ["0.5", "abc"]}
    cell.outputs = [new_output(output_type="execute_result", execution_count=1, data=test_data)]
    assert utils.determine_grade(cell) == (5, 5)


def test_determine_grade_markdown_grade_and_solution():
    cell = create_grade_and_solution_cell("test", CellType.MARKDOWN, "foo", 10)
    cell.metadata.nbgrader["checksum"] = utils.compute_checksum(cell)
    assert utils.determine_grade(cell) == (0, 10)

    cell = create_grade_and_solution_cell("test", CellType.MARKDOWN, "foo", 10)
    cell.source = "test!"
    assert utils.determine_grade(cell) == (None, 10)


def test_compute_checksum_identical():
    # is the same for two identical cells?
    cell1 = create_grade_cell("hello", CellType.CODE, "foo", 1)
    cell2 = create_grade_cell("hello", CellType.CODE, "foo", 1)
    assert utils.compute_checksum(cell1) == utils.compute_checksum(cell2)

    cell1 = create_solution_cell("hello", CellType.CODE, "foo")
    cell2 = create_solution_cell("hello", CellType.CODE, "foo")
    assert utils.compute_checksum(cell1) == utils.compute_checksum(cell2)


def test_compute_checksum_cell_type():
    # does the cell type make a difference?
    cell1 = create_grade_cell("hello", CellType.CODE, "foo", 1)
    cell2 = create_grade_cell("hello", CellType.MARKDOWN, "foo", 1)
    assert utils.compute_checksum(cell1) != utils.compute_checksum(cell2)

    cell1 = create_solution_cell("hello", CellType.CODE, "foo")
    cell2 = create_solution_cell("hello", CellType.MARKDOWN, "foo")
    assert utils.compute_checksum(cell1) != utils.compute_checksum(cell2)


def test_compute_checksum_whitespace():
    # does whitespace make no difference?
    cell1 = create_grade_cell("hello", CellType.CODE, "foo", 1)
    cell2 = create_grade_cell("hello ", CellType.CODE, "foo", 1)
    assert utils.compute_checksum(cell1) != utils.compute_checksum(cell2)

    cell1 = create_grade_cell("hello", CellType.MARKDOWN, "foo", 1)
    cell2 = create_grade_cell("hello ", CellType.MARKDOWN, "foo", 1)
    assert utils.compute_checksum(cell1) != utils.compute_checksum(cell2)

    cell1 = create_solution_cell("hello", CellType.CODE, "foo")
    cell2 = create_solution_cell("hello ", CellType.CODE, "foo")
    assert utils.compute_checksum(cell1) != utils.compute_checksum(cell2)

    cell1 = create_solution_cell("hello", CellType.MARKDOWN, "foo")
    cell2 = create_solution_cell("hello ", CellType.MARKDOWN, "foo")
    assert utils.compute_checksum(cell1) != utils.compute_checksum(cell2)


def test_compute_checksum_source():
    # does the source make a difference?
    cell1 = create_grade_cell("print('hello')", CellType.CODE, "foo", 1)
    cell2 = create_grade_cell("print( 'hello' )", CellType.CODE, "foo", 1)
    assert utils.compute_checksum(cell1) != utils.compute_checksum(cell2)

    cell1 = create_grade_cell("print('hello')", CellType.CODE, "foo", 1)
    cell2 = create_grade_cell("print( 'hello!' )", CellType.CODE, "foo", 1)
    assert utils.compute_checksum(cell1) != utils.compute_checksum(cell2)

    cell1 = create_grade_cell("print('hello')", CellType.MARKDOWN, "foo", 1)
    cell2 = create_grade_cell("print( 'hello' )", CellType.MARKDOWN, "foo", 1)
    assert utils.compute_checksum(cell1) != utils.compute_checksum(cell2)

    cell1 = create_solution_cell("print('hello')", CellType.CODE, "foo")
    cell2 = create_solution_cell("print( 'hello' )", CellType.CODE, "foo")
    assert utils.compute_checksum(cell1) != utils.compute_checksum(cell2)

    cell1 = create_solution_cell("print('hello')", CellType.CODE, "foo")
    cell2 = create_solution_cell("print( 'hello!' )", CellType.CODE, "foo")
    assert utils.compute_checksum(cell1) != utils.compute_checksum(cell2)

    cell1 = create_solution_cell("print('hello')", CellType.MARKDOWN, "foo")
    cell2 = create_solution_cell("print( 'hello' )", CellType.MARKDOWN, "foo")
    assert utils.compute_checksum(cell1) != utils.compute_checksum(cell2)


def test_compute_checksum_points():
    # does the number of points make a difference (only for grade cells)?
    cell1 = create_grade_cell("hello", CellType.CODE, "foo", 2)
    cell2 = create_grade_cell("hello", CellType.CODE, "foo", 1)
    assert utils.compute_checksum(cell1) != utils.compute_checksum(cell2)

    cell1 = create_grade_cell("hello", CellType.CODE, "foo", 2)
    cell2 = create_grade_cell("hello", CellType.CODE, "foo", 1)
    cell1.metadata.nbgrader["grade"] = False
    cell2.metadata.nbgrader["grade"] = False
    assert utils.compute_checksum(cell1) == utils.compute_checksum(cell2)


def test_compute_checksum_grade_id():
    # does the grade id make a difference (only for grade cells)?
    cell1 = create_grade_cell("hello", CellType.CODE, "foo", 1)
    cell2 = create_grade_cell("hello", CellType.CODE, "bar", 1)
    assert utils.compute_checksum(cell1) != utils.compute_checksum(cell2)

    cell1 = create_grade_cell("hello", CellType.CODE, "foo", 1)
    cell2 = create_grade_cell("hello", CellType.CODE, "bar", 1)
    cell1.metadata.nbgrader["grade"] = False
    cell2.metadata.nbgrader["grade"] = False
    assert utils.compute_checksum(cell1) != utils.compute_checksum(cell2)


def test_compute_checksum_grade_cell():
    # does it make a difference if grade=True?
    cell1 = create_grade_cell("hello", CellType.CODE, "foo", 1)
    cell2 = create_grade_cell("hello", CellType.CODE, "foo", 1)
    cell2.metadata.nbgrader["grade"] = False
    assert utils.compute_checksum(cell1) != utils.compute_checksum(cell2)


def test_compute_checksum_solution_cell():
    # does it make a difference if solution=True?
    cell1 = create_solution_cell("hello", CellType.CODE, "foo")
    cell2 = create_solution_cell("hello", CellType.CODE, "foo")
    cell2.metadata.nbgrader["solution"] = False
    assert utils.compute_checksum(cell1) != utils.compute_checksum(cell2)


def test_compute_checksum_utf8():
    utils.compute_checksum(create_solution_cell("\u03b8", CellType.MARKDOWN, "foo"))
    utils.compute_checksum(
        create_solution_cell("$$\\int^\u221e_0 x^2dx$$", CellType.MARKDOWN, "foo")
    )
