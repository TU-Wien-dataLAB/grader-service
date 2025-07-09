import os
from typing import Any

from traitlets import List

from grader_service.api.models.assignment_settings import AssignmentSettings
from grader_service.convert import utils
from grader_service.convert.converters.base import BaseConverter
from grader_service.convert.converters.baseapp import ConverterApp
from grader_service.convert.gradebook.gradebook import Gradebook, MissingEntry
from grader_service.convert.preprocessors import (
    CheckCellMetadata,
    ClearAlwaysHiddenTests,
    ClearOutput,
    DeduplicateIds,
    Execute,
    LimitOutput,
    OverwriteCells,
    OverwriteKernelspec,
    SaveAutoGrades,
)


class Autograde(BaseConverter):
    _sanitizing = True

    sanitize_preprocessors = List(
        [ClearOutput, DeduplicateIds, OverwriteKernelspec, OverwriteCells, CheckCellMetadata]
    ).tag(config=True)
    autograde_preprocessors = List(
        [Execute, LimitOutput, SaveAutoGrades, CheckCellMetadata, ClearAlwaysHiddenTests]
    ).tag(config=True)

    preprocessors = List([])

    def _init_preprocessors(self) -> None:
        self.exporter._preprocessors = []
        if self._sanitizing:
            preprocessors = self.sanitize_preprocessors
        else:
            preprocessors = self.autograde_preprocessors

        for pp in preprocessors:
            self.exporter.register_preprocessor(pp)

    def convert_single_notebook(self, notebook_filename: str) -> None:
        # ignore notebooks that aren't in the gradebook
        resources = self.init_single_notebook_resources(notebook_filename)
        with Gradebook(resources["output_json_path"]) as gb:
            try:
                gb.find_notebook(resources["unique_key"])
            except MissingEntry:
                self.log.warning("Skipping unknown notebook: %s", notebook_filename)
                return

        self.log.info("Sanitizing %s", notebook_filename)
        self._sanitizing = True
        self._init_preprocessors()
        super().convert_single_notebook(notebook_filename)

        notebook_filename = os.path.join(
            self.writer.build_directory, os.path.basename(notebook_filename)
        )
        self.log.info("Autograding %s", notebook_filename)
        self._sanitizing = False
        self._init_preprocessors()
        try:
            with utils.setenv(NBGRADER_EXECUTION="autograde"):
                super().convert_single_notebook(notebook_filename)
        finally:
            self._sanitizing = True

    def convert_notebooks(self) -> None:
        # check for missing notebooks and give them a score of zero if they do not exist
        json_path = os.path.join(self._output_directory, "gradebook.json")
        with Gradebook(json_path) as gb:
            self.copy_unmatched_files(gb)

            glob_notebooks = {
                self.init_single_notebook_resources(n)["unique_key"]: n for n in self.notebooks
            }
            for notebook in gb.model.notebook_id_set.difference(set(glob_notebooks.keys())):
                self.log.warning("No submitted file: %s", notebook)
                nb = gb.find_notebook(notebook)
                for grade in nb.grades:
                    grade.auto_score = 0
                    grade.needs_manual_grade = False
                    gb.add_grade(grade.id, notebook, grade)

        super().convert_notebooks()

    def __init__(
        self,
        input_dir: str,
        output_dir: str,
        file_pattern: str,
        assignment_settings: AssignmentSettings,
        **kwargs: Any,
    ) -> None:
        super().__init__(input_dir, output_dir, file_pattern, assignment_settings, **kwargs)
        self.force = True  # always overwrite generated assignments


class AutogradeApp(ConverterApp):
    version = ConverterApp.__version__

    def start(self):
        Autograde(
            input_dir=self.input_directory,
            output_dir=self.output_directory,
            file_pattern=self.file_pattern,
            assignment_settings=utils.get_assignment_settings_from_env(),
            config=self.config,
        ).start()
