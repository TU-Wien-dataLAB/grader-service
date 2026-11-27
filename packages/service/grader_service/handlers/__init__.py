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
    lti,
    permission,
    roles,
    submissions,
    users,
)

__all__ = [
    "assignment",
    "base_handler",
    "config",
    "git",
    "grading",
    "health",
    "lectures",
    "lti",
    "permission",
    "roles",
    "submissions",
    "users",
]
