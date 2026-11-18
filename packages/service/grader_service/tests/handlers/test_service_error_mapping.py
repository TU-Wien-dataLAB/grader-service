# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
from http import HTTPStatus

import pytest

from grader_service.errors import (
    ConflictError,
    InvalidInputError,
    NotFoundError,
    PermissionDeniedError,
    ServiceError,
)
from grader_service.handlers.base_handler import GraderErrorMixin


def test_all_direct_service_error_subclasses_are_mapped():
    """Every direct ServiceError subclass must have a SERVICE_ERROR_STATUS
    entry, otherwise the error would surface as a 500."""
    unmapped = [
        cls.__name__
        for cls in ServiceError.__subclasses__()
        if cls not in GraderErrorMixin.SERVICE_ERROR_STATUS
    ]
    assert unmapped == [], f"Service error subclasses without mapping: {unmapped}"


@pytest.mark.parametrize(
    "error, expected_status",
    [
        (NotFoundError("not found"), HTTPStatus.NOT_FOUND),
        (ConflictError("conflict"), HTTPStatus.CONFLICT),
        (InvalidInputError("invalid"), HTTPStatus.BAD_REQUEST),
        (PermissionDeniedError("denied"), HTTPStatus.FORBIDDEN),
    ],
)
def test_to_api_error_translates_status(error: ServiceError, expected_status: HTTPStatus):
    api_error = GraderErrorMixin.to_api_error(error)
    assert api_error.status_code == expected_status
    assert api_error.message == str(error)


def test_to_api_error_subclass_inherits_status():
    class LectureNotFoundError(NotFoundError):
        pass

    api_error = GraderErrorMixin.to_api_error(LectureNotFoundError("lecture not found"))
    assert api_error.status_code == HTTPStatus.NOT_FOUND


def test_to_api_error_unmapped_error_raises():
    class UnmappedError(ServiceError):
        pass

    with pytest.raises(ValueError, match="UnmappedError"):
        GraderErrorMixin.to_api_error(UnmappedError("boom"))
