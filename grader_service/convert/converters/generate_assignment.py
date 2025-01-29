
import json
import os
from sys import path
from textwrap import dedent
from typing import Any

from grader_service.api.models.assignment_settings import AssignmentSettings
from grader_service.convert.converters.base import BaseConverter
from grader_service.convert.converters.baseapp import ConverterApp
from grader_service.convert.preprocessors import (
    AddRevert,
    CheckCellMetadata,
    ClearHiddenTests,
    ClearMarkScheme,
    ClearOutput,
    ClearSolutions,
    ComputeChecksums,
    IncludeHeaderFooter,
    LockCells,
    SaveCells,
    ClearAlwaysHiddenTests
)
from traitlets import Bool, List, default
from traitlets.config.loader import Config

class GenerateAssignment(BaseConverter):
    create_assignment = Bool(
        True,
        help=dedent(
            """
            Whether to create the assignment at runtime if it does not
            already exist.
            """
        ),
    ).tag(config=True)

    @default("permissions")
    def _permissions_default(self) -> int:
        return 664

    preprocessors = List(
        [
            IncludeHeaderFooter,
            LockCells,
            ClearSolutions,
            ClearOutput,
            CheckCellMetadata,
            ComputeChecksums,
            SaveCells,
            ClearHiddenTests,
            ClearAlwaysHiddenTests,
            ClearMarkScheme,
            ComputeChecksums,
            AddRevert,
            CheckCellMetadata,
        ]
    ).tag(config=True)

    # NB: ClearHiddenTests must come after ComputeChecksums and SaveCells.
    # ComputerChecksums must come again after ClearHiddenTests.

    def _load_config(self, cfg: Config, **kwargs: Any) -> None:
        super(GenerateAssignment, self)._load_config(cfg, **kwargs)

    def __init__(
            self, input_dir: str, output_dir: str, file_pattern: str, assignment_settings: AssignmentSettings, **kwargs: Any
    ) -> None:
        super(GenerateAssignment, self).__init__(
            input_dir, output_dir, file_pattern, assignment_settings, **kwargs
        )
        self.force = True  # always overwrite generated assignments

    def start(self) -> None:
        super(GenerateAssignment, self).start()


class GenerateAssignmentApp(ConverterApp):
    version = ConverterApp.__version__
    settings_json = os.getenv("ASSIGNMENT_SETTINGS", "{}")
    assignment_settings = AssignmentSettings.from_dict(json.loads(settings_json))

    def start(self):
        GenerateAssignment(
            input_dir=self.input_directory,
            output_dir=self.output_directory,
            file_pattern=self.file_pattern,
            assignment_settings=self.assignment_settings,
            config=self.config
        ).start()
