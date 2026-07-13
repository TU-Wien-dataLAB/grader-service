import warnings
from textwrap import dedent

import pytest
from traitlets.config import Config

from grader_service.convert.preprocessors import ClearAlwaysHiddenTests

from .. import create_code_cell, create_text_cell
from .base import BaseTestPreprocessor


@pytest.fixture
def preprocessor():
    return ClearAlwaysHiddenTests()


class TestClearAlwaysHiddenTests(BaseTestPreprocessor):
    def test_remove_hidden_util_region_code(self, preprocessor):
        """Are hidden util regions in code cells correctly replaced?"""
        cell = create_code_cell()
        cell.source = dedent(
            """
            assert True
            ### BEGIN ALWAYS HIDDEN TESTS
            assert True
            ### END ALWAYS HIDDEN TESTS
            """
        ).strip()
        removed_util = preprocessor._remove_hidden_util_region(cell)
        assert removed_util
        assert cell.source == "assert True"

    def test_remove_hidden_util_region_text(self, preprocessor):
        """Are hidden util regions in text cells correctly replaced?"""
        cell = create_text_cell()
        cell.source = dedent(
            """
            something something
            ### BEGIN ALWAYS HIDDEN TESTS
            this is a util!
            ### END ALWAYS HIDDEN TESTS
            """
        ).strip()
        removed_util = preprocessor._remove_hidden_util_region(cell)
        assert removed_util
        assert cell.source == "something something"

    def test_remove_hidden_util_region_no_end(self, preprocessor):
        """Is an error thrown when there is no end always hidden util statement?"""
        cell = create_text_cell()
        cell.source = dedent(
            """
            something something
            ### BEGIN ALWAYS HIDDEN TESTS
            this is a util!
            """
        ).strip()

        with pytest.raises(RuntimeError):
            preprocessor._remove_hidden_util_region(cell)

    def test_dont_remove_hidden_util_region(self, preprocessor):
        """Is false returned when there is no hidden util region?"""
        cell = create_text_cell()
        removed_util = preprocessor._remove_hidden_util_region(cell)
        assert not removed_util

    def test_deprecated_delimeter_config(self):
        """Does the deprecated delimeter config key still work and warn?"""
        c = Config()
        c.ClearAlwaysHiddenTests.begin_util_delimeter = "MY BEGIN"
        c.ClearAlwaysHiddenTests.end_util_delimeter = "MY END"
        with pytest.warns(DeprecationWarning):
            pp = ClearAlwaysHiddenTests(config=c)
        assert pp.begin_util_delimiter == "MY BEGIN"
        assert pp.end_util_delimiter == "MY END"

    def test_new_delimiter_config_no_warning(self):
        """Does the new delimiter config key work without warning?"""
        c = Config()
        c.ClearAlwaysHiddenTests.begin_util_delimiter = "MY BEGIN"
        c.ClearAlwaysHiddenTests.end_util_delimiter = "MY END"
        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            pp = ClearAlwaysHiddenTests(config=c)
        assert pp.begin_util_delimiter == "MY BEGIN"
        assert pp.end_util_delimiter == "MY END"
