# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

from grader_service.orm.api_token import APIToken
from grader_service.orm.assignment import Assignment
from grader_service.orm.base import Base
from grader_service.orm.lecture import Lecture
from grader_service.orm.oauthclient import OAuthClient
from grader_service.orm.oauthcode import OAuthCode
from grader_service.orm.submission import Submission
from grader_service.orm.takepart import Role
from grader_service.orm.user import User

__all__ = [
    "Lecture",
    "User",
    "Role",
    "Submission",
    "Assignment",
    "Base",
    "OAuthCode",
    "OAuthClient",
    "APIToken",
]
