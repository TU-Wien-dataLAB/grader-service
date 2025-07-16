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


class GenerateFeedbackApp(ConverterApp):
    version = ConverterApp.__version__

    def start(self, assignment_settings: AssignmentSettings):
        GenerateFeedback(
            input_dir=self.input_directory,
            output_dir=self.output_directory,
            file_pattern=self.file_pattern,
            assignment_settings=utils.get_assignment_settings_from_env(),
            config=self.config,
        ).start()
