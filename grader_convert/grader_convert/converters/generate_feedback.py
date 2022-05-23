

import os
from typing import Any

from nbconvert.exporters import HTMLExporter
from nbconvert.preprocessors import CSSHTMLHeaderPreprocessor
from traitlets import List, default
from traitlets.config import Config

from grader_convert.converters.baseapp import ConverterApp
from grader_convert.preprocessors import GetGrades
from grader_convert.converters.base import BaseConverter


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
        self, input_dir: str, output_dir: str, file_pattern: str, **kwargs: Any
    ):
        super(GenerateFeedback, self).__init__(
            input_dir, output_dir, file_pattern, **kwargs
        )
        c = Config()
        # Note: nbconvert 6.0 completely changed how templates work: they can now be installed separately
        #  and can be given by name (classic is default)
        if "template" not in self.config.HTMLExporter:
            template_path = os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "templates",
                )
            )
            # '/Users/matthiasmatt/opt/miniconda3/envs/grader/share/jupyter/nbconvert/templates/classic/index.html.j2'
            c.TemplateExporter.extra_template_basedirs = template_path
            c.HTMLExporter.template_name = "feedback"
        self.update_config(c)
        self.force = True  # always overwrite generated assignments


class GenerateFeedbackApp(ConverterApp):
    version = ConverterApp.__version__

    def start(self):
        GenerateFeedback(
            input_dir=self.input_directory,
            output_dir=self.output_directory,
            file_pattern=self.file_pattern,
            config=self.config
        ).start()
