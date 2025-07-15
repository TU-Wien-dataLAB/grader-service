# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

# import handlers
from grader_service.handlers import (
    assignment,
    base_handler,
    config,
    git,
    grading,
    health,
    lectures,
    permission,
    submissions,
)
from grader_service.handlers.handler_utils import GitRepoType

__all__ = [
    "assignment",
    "grading",
    "lectures",
    "submissions",
    "git",
    "permission",
    "health",
    "config",
    "base_handler",
    "GitRepoType",
]
