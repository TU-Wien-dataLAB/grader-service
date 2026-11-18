# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
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
