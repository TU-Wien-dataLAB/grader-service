import os
from textwrap import dedent
from typing import Any

from traitlets import Bool, List, default
from traitlets.config import Config

from grader_service.api.models.assignment_settings import AssignmentSettings
from grader_service.convert import utils
from grader_service.convert.converters.base import BaseConverter
from grader_service.convert.converters.baseapp import ConverterApp
from grader_service.convert.preprocessors import (
    AddRevert,
    CheckCellMetadata,
    ClearAlwaysHiddenTests,
    ClearHiddenTests,
    ClearMarkScheme,
    ClearOutput,
    ClearSolutions,
    ComputeChecksums,
    IncludeHeaderFooter,
    LockCells,
    SaveCells,
)


class GenerateAssignment(BaseConverter):
    """Convert between the 'source code' and the 'student version' of assignment files."""

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

        # load custom configuration if it exists
        c = Config()
        custom_config_path = f"{self._input_directory}/grader_config.py"
        if os.path.exists(custom_config_path):
            local_vars = {"c": c}
            with open(custom_config_path) as f:
                code = compile(f.read(), "config.py", "exec")
                exec(code, {}, local_vars)
            c = local_vars["c"]
        c.Exporter.default_preprocessors = []
        self.update_config(c)


class GenerateAssignmentApp(ConverterApp):
    version = ConverterApp.__version__

    def start(self):
        GenerateAssignment(
            input_dir=self.input_directory,
            output_dir=self.output_directory,
            file_pattern=self.file_pattern,
            assignment_settings=utils.get_assignment_settings_from_env(),
            config=self.config,
        ).start()
