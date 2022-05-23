

# coding: utf-8

import glob
import traceback

from traitlets import default

from grader_convert.nbgraderformat import SchemaTooNewError, SchemaTooOldError
from grader_convert.validator import Validator
from grader_convert.converters.baseapp import ConverterApp

aliases = {}
flags = {
    "invert": (
        {"Validator": {"invert": True}},
        "Complain when cells pass, rather than vice versa.",
    )
}


class ValidateApp(ConverterApp):

    name = u"validate"
    description = u"Validate a notebook by running it"

    aliases = aliases
    flags = flags

    examples = """
        You can run `grader-convert validate` on just a single file, e.g.:
            grader-convert validate "Problem 1.ipynb"

        Or, you can run it on multiple files using shell globs:
            grader-convert validate "Problem Set 1/*.ipynb"

        If you want to test instead that none of the tests pass (rather than that
        all of the tests pass, which is the default), you can use --invert:
            grader-convert validate --invert "Problem 1.ipynb"
        """

    @default("classes")
    def _classes_default(self):
        classes = super(ValidateApp, self)._classes_default()
        classes.append(Validator)
        return classes

    def start(self):
        if not len(self.extra_args):
            self.fail("Must provide path to notebook:\nnbgrader validate NOTEBOOK")
        else:
            notebook_filenames = []
            for x in self.extra_args:
                notebook_filenames.extend(glob.glob(x))

        validator = Validator(parent=self)
        for filename in notebook_filenames:
            try:
                validator.validate_and_print(filename)

            except SchemaTooOldError:
                self.log.error(traceback.format_exc())
                self.fail(
                    (
                        "The notebook '{}' uses an old version "
                        "of the nbgrader metadata format. Please **back up this "
                        "notebook** and then update the metadata using:\n\nnbgrader update {}\n"
                    ).format(filename, filename)
                )

            except SchemaTooNewError:
                self.log.error(traceback.format_exc())
                self.fail(
                    (
                        "The notebook '{}' uses a newer version "
                        "of the nbgrader metadata format. Please update your version of "
                        "nbgrader to the latest version to be able to use this notebook."
                    ).format(filename)
                )

            except Exception:
                self.log.error(traceback.format_exc())
                self.fail(
                    "nbgrader encountered a fatal error while trying to validate '{}'".format(
                        filename
                    )
                )
