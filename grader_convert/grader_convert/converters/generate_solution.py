

from textwrap import dedent
from typing import Any

from traitlets import Bool, List, default
from traitlets.config.loader import Config

from grader_convert.converters.baseapp import ConverterApp
from grader_convert.preprocessors import (
    ClearMarkScheme,
    ClearOutput,
    Execute,
    IncludeHeaderFooter,
    LockCells,
)
from grader_convert.converters.base import BaseConverter


class GenerateSolution(BaseConverter):

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

    def _load_config(self, cfg: Config, **kwargs: Any) -> None:
        super(GenerateSolution, self)._load_config(cfg, **kwargs)

    preprocessors = List(
        [IncludeHeaderFooter, LockCells, ClearOutput, ClearMarkScheme, Execute]
    )
    # NB: ClearHiddenTests must come after ComputeChecksums and SaveCells.
    # ComputerChecksums must come again after ClearHiddenTests.

    def __init__(
        self, input_dir: str, output_dir: str, file_pattern: str, **kwargs: Any
    ) -> None:
        super(GenerateSolution, self).__init__(
            input_dir, output_dir, file_pattern, **kwargs
        )
        self.force = True  # always overwrite generated assignments

    def start(self) -> None:
        super(GenerateSolution, self).start()


class GenerateSolutionApp(ConverterApp):
    version = ConverterApp.__version__

    def start(self):
        GenerateSolution(
            input_dir=self.input_directory,
            output_dir=self.output_directory,
            file_pattern=self.file_pattern,
            config=self.config
        ).start()
