import json
import pytest
import os
from nbformat import validate
from nbformat.v4 import new_notebook

from grader_service.convert.preprocessors import SaveCells
from grader_service.convert.gradebook.gradebook import Gradebook
from grader_service.convert.utils import compute_checksum
from .base import BaseTestPreprocessor
from .. import (
    create_grade_cell,
    create_solution_cell,
    create_grade_and_solution_cell,
    create_locked_cell,
)


@pytest.fixture
def preprocessor():
    return SaveCells()


@pytest.fixture
def gradebook(request, json_path):
    gb = Gradebook(json_path)

    def fin():
        os.remove(json_path)

    request.addfinalizer(fin)

    return gb


@pytest.fixture
def resources(json_path):
    resources = {}
    resources["unique_key"] = "test"
    resources["output_json_file"] = "gradebook.json"
    resources["output_json_path"] = json_path
    resources["nbgrader"] = dict()  # support nbgrader pre-processors
    return resources


class TestSaveCells(BaseTestPreprocessor):
    def test_save_code_grade_cell(self, preprocessor, gradebook, resources):
        cell = create_grade_cell("hello", "code", "foo", 1)
        cell.metadata.nbgrader["checksum"] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)

        nb, resources = preprocessor.preprocess(nb, resources)

        gradebook = Gradebook(dest_json=resources["output_json_path"])
        grade_cell = gradebook.find_grade_cell("foo", "test")
        assert grade_cell.max_score == 1
        assert grade_cell.cell_type == "code"

        gradebook = Gradebook(dest_json=resources["output_json_path"])
        source_cell = gradebook.find_source_cell("foo", "test")
        assert source_cell.source == "hello"
        assert source_cell.checksum == cell.metadata.nbgrader["checksum"]
        assert source_cell.cell_type == "code"
        assert source_cell.locked

    def test_save_code_solution_cell(self, preprocessor, gradebook, resources):
        cell = create_solution_cell("hello", "code", "foo")
        cell.metadata.nbgrader["checksum"] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)

        nb, resources = preprocessor.preprocess(nb, resources)

        gradebook = Gradebook(dest_json=resources["output_json_path"])
        gradebook.find_solution_cell("foo", "test")

        source_cell = gradebook.find_source_cell("foo", "test")
        assert source_cell.source == "hello"
        assert source_cell.checksum == cell.metadata.nbgrader["checksum"]
        assert source_cell.cell_type == "code"
        assert not source_cell.locked

    def test_save_markdown_solution_cell(self, preprocessor, gradebook, resources):
        cell = create_solution_cell("hello", "markdown", "foo")
        cell.metadata.nbgrader["checksum"] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)

        nb, resources = preprocessor.preprocess(nb, resources)

        gradebook = Gradebook(dest_json=resources["output_json_path"])
        gradebook.find_solution_cell("foo", "test")

        source_cell = gradebook.find_source_cell("foo", "test")
        assert source_cell.source == "hello"
        assert source_cell.checksum == cell.metadata.nbgrader["checksum"]
        assert source_cell.cell_type == "markdown"
        assert not source_cell.locked

    def test_save_code_grade_and_solution_cell(self, preprocessor, gradebook, resources):
        cell = create_grade_and_solution_cell("hello", "code", "foo", 1)
        cell.metadata.nbgrader["checksum"] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)

        nb, resources = preprocessor.preprocess(nb, resources)

        gradebook = Gradebook(dest_json=resources["output_json_path"])
        grade_cell = gradebook.find_grade_cell("foo", "test")
        assert grade_cell.max_score == 1
        assert grade_cell.cell_type == "code"

        gradebook.find_solution_cell("foo", "test")

        source_cell = gradebook.find_source_cell("foo", "test")
        assert source_cell.source == "hello"
        assert source_cell.checksum == cell.metadata.nbgrader["checksum"]
        assert source_cell.cell_type == "code"
        assert not source_cell.locked

    def test_save_markdown_grade_and_solution_cell(self, preprocessor, gradebook, resources):
        cell = create_grade_and_solution_cell("hello", "markdown", "foo", 1)
        cell.metadata.nbgrader["checksum"] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)

        nb, resources = preprocessor.preprocess(nb, resources)

        gradebook = Gradebook(dest_json=resources["output_json_path"])
        grade_cell = gradebook.find_grade_cell("foo", "test")
        assert grade_cell.max_score == 1
        assert grade_cell.cell_type == "markdown"

        gradebook.find_solution_cell("foo", "test")

        source_cell = gradebook.find_source_cell("foo", "test")
        assert source_cell.source == "hello"
        assert source_cell.checksum == cell.metadata.nbgrader["checksum"]
        assert source_cell.cell_type == "markdown"
        assert not source_cell.locked

    def test_save_locked_code_cell(self, preprocessor, gradebook, resources):
        cell = create_locked_cell("hello", "code", "foo")
        cell.metadata.nbgrader["checksum"] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)

        nb, resources = preprocessor.preprocess(nb, resources)

        gradebook = Gradebook(dest_json=resources["output_json_path"])
        source_cell = gradebook.find_source_cell("foo", "test")
        assert source_cell.source == "hello"
        assert source_cell.checksum == cell.metadata.nbgrader["checksum"]
        assert source_cell.cell_type == "code"
        assert source_cell.locked

    def test_save_locked_markdown_cell(self, preprocessor, gradebook, resources):
        cell = create_locked_cell("hello", "markdown", "foo")
        cell.metadata.nbgrader["checksum"] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)

        nb, resources = preprocessor.preprocess(nb, resources)

        gradebook = Gradebook(dest_json=resources["output_json_path"])
        source_cell = gradebook.find_source_cell("foo", "test")
        assert source_cell.source == "hello"
        assert source_cell.checksum == cell.metadata.nbgrader["checksum"]
        assert source_cell.cell_type == "markdown"
        assert source_cell.locked

    def test_save_new_cell(self, preprocessor, gradebook, resources):
        cell1 = create_grade_and_solution_cell("hello", "markdown", "foo", 2)
        cell2 = create_grade_and_solution_cell("hello", "markdown", "bar", 1)

        nb = new_notebook()
        nb.cells.append(cell1)
        nb, resources = preprocessor.preprocess(nb, resources)

        gradebook = Gradebook(dest_json=resources["output_json_path"])
        notebook = gradebook.find_notebook("test")
        assert len(notebook.grade_cells) == 1
        assert len(notebook.solution_cells) == 1
        assert len(notebook.source_cells) == 1

        nb.cells.append(cell2)
        nb, resources = preprocessor.preprocess(nb, resources)

        gradebook = Gradebook(dest_json=resources["output_json_path"])
        notebook = gradebook.find_notebook("test")
        assert len(notebook.grade_cells) == 2
        assert len(notebook.solution_cells) == 2
        assert len(notebook.source_cells) == 2

    def test_remove_cell(self, preprocessor, gradebook, resources):
        cell1 = create_grade_and_solution_cell("hello", "markdown", "foo", 2)
        cell2 = create_grade_and_solution_cell("hello", "markdown", "bar", 1)

        nb = new_notebook()
        nb.cells.append(cell1)
        nb.cells.append(cell2)
        nb, resources = preprocessor.preprocess(nb, resources)

        gradebook = Gradebook(dest_json=resources["output_json_path"])
        notebook = gradebook.find_notebook("test")
        assert len(notebook.grade_cells) == 2
        assert len(notebook.solution_cells) == 2
        assert len(notebook.source_cells) == 2

        nb.cells = nb.cells[:-1]
        nb, resources = preprocessor.preprocess(nb, resources)

        gradebook = Gradebook(dest_json=resources["output_json_path"])
        notebook = gradebook.find_notebook("test")
        assert len(notebook.grade_cells) == 1
        assert len(notebook.solution_cells) == 1
        assert len(notebook.source_cells) == 1

    def test_modify_cell(self, preprocessor, gradebook, resources):
        nb = new_notebook()
        nb.cells.append(create_grade_and_solution_cell("hello", "markdown", "foo", 2))
        nb, resources = preprocessor.preprocess(nb, resources)

        gradebook = Gradebook(dest_json=resources["output_json_path"])
        grade_cell = gradebook.find_grade_cell("foo", "test")
        solution_cell = gradebook.find_solution_cell("foo", "test")
        source_cell = gradebook.find_source_cell("foo", "test")
        assert grade_cell.max_score == 2
        assert source_cell.source == "hello"

        nb.cells[-1] = create_grade_and_solution_cell("goodbye", "markdown", "foo", 1)
        nb, resources = preprocessor.preprocess(nb, resources)

        gradebook = Gradebook(dest_json=resources["output_json_path"])
        grade_cell = gradebook.find_grade_cell("foo", "test")
        solution_cell = gradebook.find_solution_cell("foo", "test")
        source_cell = gradebook.find_source_cell("foo", "test")
        assert solution_cell is not None
        assert grade_cell.max_score == 1
        assert source_cell.source == "goodbye"

    def test_save_kernelspec(self, preprocessor, gradebook, resources):
        kernelspec = dict(display_name="blarg", name="python3", language="python")

        nb = new_notebook()
        nb.metadata["kernelspec"] = kernelspec
        nb, resources = preprocessor.preprocess(nb, resources)

        validate(nb)
        gradebook = Gradebook(dest_json=resources["output_json_path"])
        notebook = gradebook.find_notebook("test")
        assert json.loads(notebook.kernelspec) == kernelspec
