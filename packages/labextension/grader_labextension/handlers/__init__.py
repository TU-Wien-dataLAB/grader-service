# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

from grader_labextension.handlers import (
    assignment,
    base_handler,
    config,
    grading,
    lectures,
    permission,
    submissions,
    version_control,
)

__all__ = [
    "assignment",
    "grading",
    "config",
    "lectures",
    "submissions",
    "permission",
    "version_control",
    "base_handler",
]
