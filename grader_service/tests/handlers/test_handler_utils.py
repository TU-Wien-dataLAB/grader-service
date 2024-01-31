import pytest
from tornado.web import HTTPError
from http import HTTPStatus

from grader_service.handlers.handler_utils import parse_ids



async def test_parse_not_numerical_ids():
    with pytest.raises(HTTPError) as e:
        parse_ids(-5, "not a number")
    assert e.value.status_code == HTTPStatus.BAD_REQUEST
