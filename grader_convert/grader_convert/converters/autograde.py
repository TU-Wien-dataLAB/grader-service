

import os
from textwrap import dedent
from typing import Any

from traitlets import Bool, Dict, List
from traitlets.config.loader import Config

from grader_convert import utils
from grader_convert.gradebook.gradebook import Gradebook, MissingEntry
from grader_convert.preprocessors import (
    CheckCellMetadata,
    ClearOutput,
    DeduplicateIds,
    Execute,
    LimitOutput,
    OverwriteCells,
    OverwriteKernelspec,
    SaveAutoGrades,
)
from grader_convert.converters.base import BaseConverter
from grader_convert.converters.baseapp import ConverterApp


class Autograde(BaseConverter):
    _sanitizing = True

    sanitize_preprocessors = List(
        [
            ClearOutput,
            DeduplicateIds,
            OverwriteKernelspec,
            OverwriteCells,
            CheckCellMetadata,
        ]
    ).tag(config=True)
    autograde_preprocessors = List(
        [Execute, LimitOutput, SaveAutoGrades, CheckCellMetadata]
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
        super(Autograde, self).convert_single_notebook(notebook_filename)

        notebook_filename = os.path.join(
            self.writer.build_directory, os.path.basename(notebook_filename)
        )
        self.log.info("Autograding %s", notebook_filename)
        self._sanitizing = False
        self._init_preprocessors()
        try:
            with utils.setenv(NBGRADER_EXECUTION="autograde"):
                super(Autograde, self).convert_single_notebook(notebook_filename)
        finally:
            self._sanitizing = True

    def convert_notebooks(self) -> None:
        # check for missing notebooks and give them a score of zero if they do not exist
        json_path = os.path.join(self._output_directory, "gradebook.json")
        with Gradebook(json_path) as gb:
            glob_notebooks = {
                self.init_single_notebook_resources(n)["unique_key"]: n
                for n in self.notebooks
            }
            for notebook in gb.model.notebook_id_set.difference(
                set(glob_notebooks.keys())
            ):
                self.log.warning(
                    "No submitted file: {}".format(glob_notebooks[notebook])
                )
                nb = gb.find_notebook(notebook)
                for grade in nb.grades:
                    grade.auto_score = 0
                    grade.needs_manual_grade = False
                    gb.add_grade(grade.id, notebook, grade)

        super().convert_notebooks()

    def _load_config(self, cfg: Config, **kwargs: Any) -> None:
        super(Autograde, self)._load_config(cfg, **kwargs)

    def __init__(
        self, input_dir: str, output_dir: str, file_pattern: str, **kwargs: Any
    ) -> None:
        super(Autograde, self).__init__(input_dir, output_dir, file_pattern, **kwargs)
        self.force = True  # always overwrite generated assignments

    def start(self) -> None:
        super(Autograde, self).start()


class AutogradeApp(ConverterApp):
    version = ConverterApp.__version__

    def start(self):
        Autograde(
            input_dir=self.input_directory,
            output_dir=self.output_directory,
            file_pattern=self.file_pattern,
            config=self.config
        ).start()
