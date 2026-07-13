import os
import warnings
from textwrap import dedent

import pytest
from traitlets.config import Config

from grader_service.convert.preprocessors import ClearMarkScheme

from .. import create_code_cell, create_task_cell, create_text_cell
from .base import BaseTestPreprocessor


@pytest.fixture
def preprocessor():
    return ClearMarkScheme()


class TestClearMarkScheme(BaseTestPreprocessor):
    def test_remove_mark_scheme_region_code(self, preprocessor):
        """Are mark scheme regions in code cells correctly replaced?"""
        source = dedent(
            """
            assert True
            ### BEGIN MARK SCHEME
            assert True
            ### END MARK SCHEME
            """
        ).strip()
        cell = create_task_cell(source, "markdown", "some-task-id", 2)
        removed_test = preprocessor._remove_mark_scheme_region(cell)
        assert removed_test
        assert cell.source == "assert True"

    def test_remove_mark_scheme_region_no_end(self, preprocessor):
        """Is an error thrown when there is no end hidden test statement?"""
        source = dedent(
            """
            something something
            ### BEGIN MARK SCHEME
            this is a test!
            """
        ).strip()
        cell = create_task_cell(source, "markdown", "some-task-id", 2)

        with pytest.raises(RuntimeError):
            preprocessor._remove_mark_scheme_region(cell)

    def test_remove_mark_scheme_region_nested_solution(self, preprocessor):
        """Is an error thrown when there are nested hidden test statements?"""
        source = dedent(
            """
            something something
            ### BEGIN MARK SCHEME
            ### BEGIN MARK SCHEME
            this is a test!
            """
        ).strip()
        cell = create_task_cell(source, "markdown", "some-task-id", 2)

        with pytest.raises(RuntimeError):
            preprocessor._remove_mark_scheme_region(cell)

    def test_preprocess_code_cell_mark_scheme_region(self, preprocessor):
        """Is an error thrown when there is a mark region but it's not a task cell?"""
        cell = create_code_cell()
        cell.source = dedent(
            """
            assert True
            ### BEGIN MARK SCHEME
            assert True
            ### END MARK SCHEME
            """
        ).strip()
        resources = dict()
        with pytest.raises(RuntimeError):
            preprocessor.preprocess_cell(cell, resources, 1)

    def test_preprocess_text_cell_metadata(self, preprocessor):
        """Is an error thrown when a mark scheme region exists in a non-task text cell?"""
        cell = create_text_cell()
        cell.source = dedent(
            """
            assert True
            ### BEGIN MARK SCHEME
            assert True
            ### END MARK SCHEME
            """
        ).strip()

        resources = dict()
        with pytest.raises(RuntimeError):
            preprocessor.preprocess_cell(cell, resources, 1)

        # now disable enforcing metadata
        preprocessor.enforce_metadata = False
        cell, _ = preprocessor.preprocess_cell(cell, resources, 1)
        assert cell.source == "assert True"
        assert "nbgrader" not in cell.metadata

    def test_dont_remove_mark_scheme_region(self, preprocessor):
        """Is false returned when there is no hidden test region?"""
        source = "nothing to remove"
        cell = create_task_cell(source, "markdown", "some-task-id", 2)
        removed_test = preprocessor._remove_mark_scheme_region(cell)
        assert not removed_test

    def test_preprocess_notebook(self, preprocessor):
        """Is the test notebook processed without error?"""
        nb = self._read_nb(os.path.join("files", "test_taskcell.ipynb"))
        preprocessor.preprocess(nb, {})

    def test_deprecated_delimeter_config(self):
        """Does the deprecated delimeter config key still work and warn?"""
        c = Config()
        c.ClearMarkScheme.begin_mark_scheme_delimeter = "MY BEGIN"
        c.ClearMarkScheme.end_mark_scheme_delimeter = "MY END"
        with pytest.warns(DeprecationWarning):
            pp = ClearMarkScheme(config=c)
        assert pp.begin_mark_scheme_delimiter == "MY BEGIN"
        assert pp.end_mark_scheme_delimiter == "MY END"

    def test_new_delimiter_config_no_warning(self):
        """Does the new delimiter config key work without warning?"""
        c = Config()
        c.ClearMarkScheme.begin_mark_scheme_delimiter = "MY BEGIN"
        c.ClearMarkScheme.end_mark_scheme_delimiter = "MY END"
        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            pp = ClearMarkScheme(config=c)
        assert pp.begin_mark_scheme_delimiter == "MY BEGIN"
        assert pp.end_mark_scheme_delimiter == "MY END"
