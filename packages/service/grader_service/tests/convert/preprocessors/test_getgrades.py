import os

import pytest
from nbformat.v4 import new_notebook, new_output

from grader_service.convert.gradebook.gradebook import Gradebook
from grader_service.convert.preprocessors import GetGrades, SaveAutoGrades, SaveCells
from grader_service.convert.utils import compute_checksum

from .. import create_grade_and_solution_cell, create_grade_cell, create_solution_cell
from .base import BaseTestPreprocessor


@pytest.fixture
def preprocessors():
    return (SaveCells(), SaveAutoGrades(), GetGrades())


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


class TestGetGrades(BaseTestPreprocessor):
    def test_save_correct_code(self, preprocessors, gradebook: Gradebook, resources):
        """Is a passing code cell correctly graded?"""
        cell = create_grade_cell("hello", "code", "foo", 1)
        cell.metadata.nbgrader["checksum"] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)
        preprocessors[0].preprocess(nb, resources)
        preprocessors[1].preprocess(nb, resources)
        preprocessors[2].preprocess(nb, resources)

        assert cell.metadata.nbgrader["score"] == 1
        assert cell.metadata.nbgrader["points"] == 1
        assert "comment" not in cell.metadata.nbgrader

    def test_save_incorrect_code(self, preprocessors, gradebook, resources):
        """Is a failing code cell correctly graded?"""
        cell = create_grade_cell("hello", "code", "foo", 1)
        cell.metadata.nbgrader["checksum"] = compute_checksum(cell)
        cell.outputs = [
            new_output("error", ename="NotImplementedError", evalue="", traceback=["error"])
        ]
        nb = new_notebook()
        nb.cells.append(cell)
        preprocessors[0].preprocess(nb, resources)
        preprocessors[1].preprocess(nb, resources)
        preprocessors[2].preprocess(nb, resources)

        assert cell.metadata.nbgrader["score"] == 0
        assert cell.metadata.nbgrader["points"] == 1
        assert "comment" not in cell.metadata.nbgrader

    def test_save_unchanged_code(self, preprocessors, gradebook, resources):
        """Is an unchanged code cell given the correct comment?"""
        cell = create_solution_cell("hello", "code", "foo")
        cell.metadata.nbgrader["checksum"] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)
        preprocessors[0].preprocess(nb, resources)
        preprocessors[1].preprocess(nb, resources)
        preprocessors[2].preprocess(nb, resources)

        assert cell.metadata.nbgrader["comment"] == "No response."

    def test_save_changed_code(self, preprocessors, gradebook, resources):
        """Is an unchanged code cell given the correct comment?"""
        cell = create_solution_cell("hello", "code", "foo")
        cell.metadata.nbgrader["checksum"] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)
        preprocessors[0].preprocess(nb, resources)
        cell.source = "hello!"
        preprocessors[1].preprocess(nb, resources)
        preprocessors[2].preprocess(nb, resources)

        assert cell.metadata.nbgrader["comment"] is None

    def test_save_unchanged_markdown(self, preprocessors, gradebook, resources):
        """Is an unchanged markdown cell correctly graded?"""
        cell = create_grade_and_solution_cell("hello", "markdown", "foo", 1)
        cell.metadata.nbgrader["checksum"] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)
        preprocessors[0].preprocess(nb, resources)
        preprocessors[1].preprocess(nb, resources)
        preprocessors[2].preprocess(nb, resources)

        assert cell.metadata.nbgrader["score"] == 0
        assert cell.metadata.nbgrader["points"] == 1
        assert cell.metadata.nbgrader["comment"] == "No response."

    def test_save_changed_markdown(self, preprocessors, gradebook, resources):
        """Is a changed markdown cell correctly graded?"""
        cell = create_grade_and_solution_cell("hello", "markdown", "foo", 1)
        cell.metadata.nbgrader["checksum"] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)
        preprocessors[0].preprocess(nb, resources)
        cell.source = "hello!"
        preprocessors[1].preprocess(nb, resources)
        preprocessors[2].preprocess(nb, resources)

        assert cell.metadata.nbgrader["score"] == 0
        assert cell.metadata.nbgrader["points"] == 1

        assert cell.metadata.nbgrader["comment"] is None
