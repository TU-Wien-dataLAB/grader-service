import os
from typing import Any

from nbconvert.exporters import HTMLExporter
from nbconvert.preprocessors import CSSHTMLHeaderPreprocessor
from traitlets import List, default
from traitlets.config import Config

from grader_service.api.models.assignment_settings import AssignmentSettings
from grader_service.convert import utils
from grader_service.convert.converters.base import BaseConverter
from grader_service.convert.converters.baseapp import ConverterApp
from grader_service.convert.gradebook.gradebook import Gradebook
from grader_service.convert.preprocessors import GetGrades


class GenerateFeedback(BaseConverter):
    preprocessors = List([GetGrades, CSSHTMLHeaderPreprocessor]).tag(config=True)

    @default("classes")
    def _classes_default(self):
        classes = super(GenerateFeedback, self)._classes_default()
        classes.append(HTMLExporter)
        return classes

    @default("export_class")
    def _exporter_class_default(self):
        return HTMLExporter

    @default("permissions")
    def _permissions_default(self):
        return 664

    def __init__(
        self,
        input_dir: str,
        output_dir: str,
        file_pattern: str,
        assignment_settings: AssignmentSettings,
        **kwargs: Any,
    ):
        super(GenerateFeedback, self).__init__(
            input_dir, output_dir, file_pattern, assignment_settings, **kwargs
        )
        c = Config()
        # Note: nbconvert 6.0 completely changed how templates work: they can now be installed separately
        #  and can be given by name (classic is default)
        if "template" not in self.config.HTMLExporter:
            template_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "templates")
            )
            # '/Users/matthiasmatt/opt/miniconda3/envs/grader/share/jupyter/nbconvert/templates/classic/index.html.j2'
            c.TemplateExporter.extra_template_basedirs = template_path
            c.HTMLExporter.template_name = "feedback"
        self.update_config(c)
        self.force = True  # always overwrite generated assignments

    def init_notebooks(self) -> None:
        super().init_notebooks()
        json_path = os.path.join(self._output_directory, "gradebook.json")
        with Gradebook(json_path) as gb:
            # `self.notebooks` contains the notebooks actually submitted by the student.
            # `notebook_id_set` contains the original notebooks from the assignment.
            # We generate feedback for the notebooks belonging to these both sets.
            student_nbs = {
                self.init_single_notebook_resources(nb)["unique_key"]: nb for nb in self.notebooks
            }
            assign_nb_ids = gb.model.notebook_id_set
            self.notebooks = [path for id, path in student_nbs.items() if id in assign_nb_ids]

        if len(self.notebooks) == 0:
            self.log.warning("No notebooks to generate feedback")

    def get_include_patterns(self, gb: Gradebook) -> list[str]:
        """Get glob patterns specifying for which submission files to generate feedback.

        In case of feedback generation, it can only be done for the notebooks
        which were included in the original assignment.
        """
        return self.notebooks


class GenerateFeedbackApp(ConverterApp):
    version = ConverterApp.__version__

    def start(self):
        GenerateFeedback(
            input_dir=self.input_directory,
            output_dir=self.output_directory,
            file_pattern=self.file_pattern,
            assignment_settings=utils.get_assignment_settings_from_env(),
            config=self.config,
        ).start()
