# Copyright (c) 2025, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
import io
import logging
import os
import shutil
import stat
import sys
from contextlib import contextmanager
from typing import Iterator

from traitlets import TraitError
from traitlets.config.configurable import LoggerType


def rmtree(path: str) -> None:
    """Python version-independent function to remove a directory tree.

    Exceptions are handled by the `rm_error` handler.
    In `shutil.rmtree`, `onerror` is deprecated in 3.12 and `onexc` is introduced instead.

    :param path: Path pointing to the directory to remove.
    :type path: str
    """
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=rm_error)
    else:
        shutil.rmtree(path, onerror=rm_error)


def rm_error(func, path, exc_info):
    if not os.access(path, os.W_OK):
        # Is the error an access error ?
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise


@contextmanager
def collect_logs(logger: LoggerType) -> Iterator[io.StringIO]:
    """
    A context manager for collecting logs from a logger.

    Adds a `StreamHandler` to the `logger` and yields a log stream, whose content
    can then be retrieved with `log_stream.getvalue().

    Example usage for collecting `Autograde` logs:

    .. code-block:: python

        autograder = Autograde(...)
        with collect_logs(autograder.log) as log_stream:
            autograder.start()
            grading_logs = log_stream.getvalue()

    """
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setFormatter(
        logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
    )
    logger.addHandler(handler)
    try:
        yield log_stream
    finally:
        logger.removeHandler(handler)
        handler.close()


def executable_validator(proposal: dict) -> str:
    exec: str = proposal["value"]
    if shutil.which(exec) is None:
        raise TraitError(f"The executable is not valid: {exec}")
    return exec
