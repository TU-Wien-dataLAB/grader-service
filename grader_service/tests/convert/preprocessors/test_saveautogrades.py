import pytest
import os
from nbformat.v4 import new_notebook, new_output

from grader_service.convert.preprocessors import SaveCells, SaveAutoGrades
from grader_service.convert.gradebook.gradebook import Gradebook
from grader_service.convert.utils import compute_checksum
from .base import BaseTestPreprocessor
from .. import create_grade_cell, create_grade_and_solution_cell, create_solution_cell


@pytest.fixture
def preprocessors():
    return (SaveCells(), SaveAutoGrades())


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


class TestSaveAutoGrades(BaseTestPreprocessor):
    def test_grade_correct_code(self, preprocessors, gradebook, resources):
        """Is a passing code cell correctly graded?"""
        cell = create_grade_cell("hello", "code", "foo", 1)
        cell.metadata.nbgrader["checksum"] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)
        preprocessors[0].preprocess(nb, resources)
        preprocessors[1].preprocess(nb, resources)

        gradebook = Gradebook(dest_json=resources["output_json_path"])
        grade_cell = gradebook.find_grade("foo", "test")
        assert grade_cell.score == 1
        assert grade_cell.max_score == 1
        assert grade_cell.auto_score == 1
        assert grade_cell.manual_score == None
        assert not grade_cell.needs_manual_grade

    def test_grade_incorrect_code(self, preprocessors, gradebook, resources):
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

        gradebook = Gradebook(dest_json=resources["output_json_path"])
        grade_cell = gradebook.find_grade("foo", "test")
        assert grade_cell.score == 0
        assert grade_cell.max_score == 1
        assert grade_cell.auto_score == 0
        assert grade_cell.manual_score == None
        assert not grade_cell.needs_manual_grade

    def test_grade_unchanged_markdown(self, preprocessors, gradebook, resources):
        """Is an unchanged markdown cell correctly graded?"""
        cell = create_grade_and_solution_cell("hello", "markdown", "foo", 1)
        cell.metadata.nbgrader["checksum"] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)
        preprocessors[0].preprocess(nb, resources)
        preprocessors[1].preprocess(nb, resources)

        gradebook = Gradebook(dest_json=resources["output_json_path"])
        grade_cell = gradebook.find_grade("foo", "test")
        assert grade_cell.score == 0
        assert grade_cell.max_score == 1
        assert grade_cell.auto_score == 0
        assert grade_cell.manual_score == None
        assert not grade_cell.needs_manual_grade

    def test_grade_changed_markdown(self, preprocessors, gradebook, resources):
        """Is a changed markdown cell correctly graded?"""
        cell = create_grade_and_solution_cell("hello", "markdown", "foo", 1)
        cell.metadata.nbgrader["checksum"] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)
        preprocessors[0].preprocess(nb, resources)
        cell.source = "hello!"
        preprocessors[1].preprocess(nb, resources)

        gradebook = Gradebook(dest_json=resources["output_json_path"])
        grade_cell = gradebook.find_grade("foo", "test")
        assert grade_cell.score == 0
        assert grade_cell.max_score == 1
        assert grade_cell.auto_score == None
        assert grade_cell.manual_score == None
        assert grade_cell.needs_manual_grade

    def test_comment_unchanged_code(self, preprocessors, gradebook, resources):
        """Is an unchanged code cell given the correct comment?"""
        cell = create_solution_cell("hello", "code", "foo")
        cell.metadata.nbgrader["checksum"] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)
        preprocessors[0].preprocess(nb, resources)
        preprocessors[1].preprocess(nb, resources)

        gradebook = Gradebook(dest_json=resources["output_json_path"])
        comment = gradebook.find_comment("foo", "test")
        assert comment.auto_comment == "No response."

    def test_comment_changed_code(self, preprocessors, gradebook, resources):
        """Is a changed code cell given the correct comment?"""
        cell = create_solution_cell("hello", "code", "foo")
        cell.metadata.nbgrader["checksum"] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)
        preprocessors[0].preprocess(nb, resources)
        cell.source = "hello!"
        preprocessors[1].preprocess(nb, resources)

        gradebook = Gradebook(dest_json=resources["output_json_path"])
        comment = gradebook.find_comment("foo", "test")
        assert comment.auto_comment is None

    def test_comment_unchanged_markdown(self, preprocessors, gradebook, resources):
        """Is an unchanged markdown cell given the correct comment?"""
        cell = create_grade_and_solution_cell("hello", "markdown", "foo", 1)
        cell.metadata.nbgrader["checksum"] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)
        preprocessors[0].preprocess(nb, resources)
        preprocessors[1].preprocess(nb, resources)

        gradebook = Gradebook(dest_json=resources["output_json_path"])
        comment = gradebook.find_comment("foo", "test")
        assert comment.auto_comment == "No response."

    def test_comment_changed_markdown(self, preprocessors, gradebook, resources):
        """Is a changed markdown cell given the correct comment?"""
        cell = create_grade_and_solution_cell("hello", "markdown", "foo", 1)
        cell.metadata.nbgrader["checksum"] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)
        preprocessors[0].preprocess(nb, resources)
        cell.source = "hello!"
        preprocessors[1].preprocess(nb, resources)

        gradebook = Gradebook(dest_json=resources["output_json_path"])
        comment = gradebook.find_comment("foo", "test")
        assert comment.auto_comment is None

    def test_grade_existing_manual_grade(self, preprocessors, gradebook, resources):
        """Is a failing code cell correctly graded?"""
        cell = create_grade_and_solution_cell("hello", "markdown", "foo", 1)
        nb = new_notebook()
        nb.cells.append(cell)
        preprocessors[0].preprocess(nb, resources)
        cell.source = "hello!"
        preprocessors[1].preprocess(nb, resources)

        gradebook = Gradebook(dest_json=resources["output_json_path"])
        grade_cell = gradebook.find_grade("foo", "test")
        assert grade_cell.score == 0
        assert grade_cell.max_score == 1
        assert grade_cell.auto_score == None
        assert grade_cell.manual_score == None
        assert grade_cell.needs_manual_grade

        grade_cell.manual_score = 1
        grade_cell.needs_manual_grade = False
        gradebook.write_model()

        preprocessors[1].preprocess(nb, resources)

        gradebook = Gradebook(dest_json=resources["output_json_path"])
        grade_cell = gradebook.find_grade("foo", "test")
        assert grade_cell.score == 1
        assert grade_cell.max_score == 1
        assert grade_cell.auto_score == None
        assert grade_cell.manual_score == 1
        assert grade_cell.needs_manual_grade

    def test_grade_existing_auto_comment(self, preprocessors, gradebook, resources):
        """Is a failing code cell correctly graded?"""
        cell = create_grade_and_solution_cell("hello", "markdown", "foo", 1)
        cell.metadata.nbgrader["checksum"] = compute_checksum(cell)
        nb = new_notebook()
        nb.cells.append(cell)
        preprocessors[0].preprocess(nb, resources)
        preprocessors[1].preprocess(nb, resources)

        gradebook = Gradebook(dest_json=resources["output_json_path"])
        comment = gradebook.find_comment("foo", "test")
        assert comment.auto_comment == "No response."

        nb.cells[-1].source = "goodbye"
        preprocessors[1].preprocess(nb, resources)

        gradebook = Gradebook(dest_json=resources["output_json_path"])
        comment = gradebook.find_comment("foo", "test")
        assert comment.auto_comment is None
