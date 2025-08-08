# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
import enum
from http import HTTPStatus
from typing import Union

from tornado.web import HTTPError


def parse_ids(*args) -> Union[int, tuple[int, ...]]:
    """
    Validates that provided args are all integers.

    :param args: certain amount of id (int) values
    :return: tuple of ids as ints, or a single id if only one was provided
    :raises HTTPError: if args contain invalid ids which cannot be cast to int
    """
    try:
        ids = tuple(int(id) for id in args)
    except ValueError:
        raise HTTPError(HTTPStatus.BAD_REQUEST, reason="All IDs have to be numerical")
    if len(ids) == 1:
        return ids[0]
    return ids


class GitRepoType(enum.StrEnum):
    """Allowed repository types.

    SOURCE: The source files created by the instructor.
    RELEASE: The "student" version of the source files.
    USER: A user's copy of the release files, which can be submitted.
    AUTOGRADE: Autograded submission files.
    EDIT: Copy of the submission files, created by the instructor for manual editing.
    FEEDBACK: Final feedback for a submission.
    """

    SOURCE = "source"
    RELEASE = "release"
    USER = "user"
    AUTOGRADE = "autograde"
    EDIT = "edit"
    FEEDBACK = "feedback"
