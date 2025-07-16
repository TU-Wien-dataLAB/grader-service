# Copyright (c) 2025, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
import os
import shutil
import stat
import sys


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
