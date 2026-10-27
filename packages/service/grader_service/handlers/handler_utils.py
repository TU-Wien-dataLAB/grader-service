# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
from http import HTTPStatus
from typing import Optional, Union

import tornado.escape
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


def get_int_argument(
    handler, name: str, default: int, minimum: int = None, maximum: int = None
) -> int:
    """
    Parses an integer query argument from a request handler,
    raising HTTPError 400 for invalid or out-of-range values.

    :param handler: the request handler owning the query arguments
    :param name: name of the query argument
    :param default: default value if the argument is absent
    :param minimum: lower bound (inclusive)
    :param maximum: upper bound (inclusive)
    :return: the parsed integer value
    :raises HTTPError: if the value is not an integer or out of range
    """
    raw = handler.get_argument(name, default)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise HTTPError(HTTPStatus.BAD_REQUEST, reason=f"Invalid {name}: must be an integer")
    if minimum is not None and value < minimum:
        raise HTTPError(HTTPStatus.BAD_REQUEST, reason=f"Invalid {name}: must be >= {minimum}")
    if maximum is not None and value > maximum:
        raise HTTPError(HTTPStatus.BAD_REQUEST, reason=f"Invalid {name}: must be <= {maximum}")
    return value


def get_bool_argument(handler, name: str, default: Optional[bool] = None) -> Optional[bool]:
    """
    Parses a boolean query argument from a request handler,
    raising HTTPError 400 for invalid values.

    Only the strings "true" and "false" are accepted; any other value
    (e.g. "1", "yes") is rejected so that misspelled flags do not
    silently default to false.

    :param handler: the request handler owning the query arguments
    :param name: name of the query argument
    :param default: default value if the argument is absent
    :return: the parsed boolean value
    :raises HTTPError: if the value is not "true" or "false"
    """
    raw = handler.get_argument(name, None)
    if raw is None:
        return default
    if raw == "true":
        return True
    if raw == "false":
        return False
    raise HTTPError(HTTPStatus.BAD_REQUEST, reason=f"Invalid {name}: must be 'true' or 'false'")


def parse_json_dto(handler, dto_cls):
    """
    Decodes the JSON request body into the given DTO class,
    raising HTTPError 400 for malformed payloads.

    :param handler: the request handler owning the request body
    :param dto_cls: the DTO class to deserialize the body into
    :return: the deserialized DTO
    :raises HTTPError: if the body is not valid JSON or cannot be deserialized
    """
    try:
        body = tornado.escape.json_decode(handler.request.body)
        return dto_cls.from_dict(body)
    except ValueError:
        raise HTTPError(HTTPStatus.BAD_REQUEST, reason="Invalid request body")
