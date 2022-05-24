

import logging
import os
import sys

from jupyter_core.application import JupyterApp
from traitlets.config.application import Application
from traitlets.traitlets import Unicode, validate, TraitError

from .._version import __version__

base_converter_aliases = {
    "log-level": "Application.log_level",
    "i": "ConverterApp.input_directory",
    "o": "ConverterApp.output_directory",
    "p": "ConverterApp.file_pattern",
    "input_directory": "ConverterApp.input_directory",
    "output_directory": "ConverterApp.output_directory",
    "file_pattern": "ConverterApp.file_pattern",
}
base_converter_flags = {
    "debug": (
        {"Application": {"log_level": "DEBUG"}},
        "set log level to DEBUG (maximize logging output)",
    ),
    "quiet": (
        {"Application": {"log_level": "CRITICAL"}},
        "set log level to CRITICAL (minimize logging output)",
    ),
}


class ConverterApp(Application):
    description = """Base app for converters
    """

    __version__ = __version__

    aliases = base_converter_aliases
    flags = base_converter_flags

    input_directory = Unicode(None, allow_none=False).tag(config=True)
    output_directory = Unicode(None, allow_none=False).tag(config=True)
    file_pattern = Unicode("*.ipynb", allow_none=False).tag(config=True)

    def _log_level_default(self):
        return logging.INFO

    @validate("input_directory", "output_directory")
    def _dir_exits(self, proposal) -> str:
        if os.path.isdir(proposal["value"]):
            return proposal["value"]
        else:
            self.log.error(f'The path {proposal.value} of {proposal.trait.name} is not a directory')
            raise TraitError(f'The path {proposal.value} of {proposal.trait.name} is not a directory')

    def fail(self, msg, *args):
        """Log the error msg using self.log.error and exit using sys.exit(1)."""
        self.log.error(msg, *args)
        sys.exit(1)
