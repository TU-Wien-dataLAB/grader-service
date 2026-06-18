# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import json
import os
from typing import Callable, Dict, Optional, Union
from urllib.parse import ParseResultBytes, quote_plus, urlencode, urlparse

from tornado.escape import json_decode
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPResponse
from traitlets.config.configurable import SingletonConfigurable
from traitlets.traitlets import TraitError, Unicode, validate


class RequestService(SingletonConfigurable):
    url = Unicode(os.environ.get("GRADER_HOST_URL", "http://127.0.0.1:4010"))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.http_client = AsyncHTTPClient()
        self._service_cookie = None

    async def request(
        self,
        method: str,
        endpoint: str,
        body: Union[dict, str] = None,
        header: Dict[str, str] = None,
        decode_response: bool = True,
        request_timeout: float = 20.0,
        connect_timeout: float = 20.0,
        response_callback: Optional[Callable[[HTTPResponse], None]] = None,
    ) -> Union[dict, list, HTTPResponse]:
        self.log.info(self.url + endpoint)
        if self._service_cookie:
            header["Cookie"] = self._service_cookie

        if isinstance(body, dict):
            body = json.dumps(body)

        # Build HTTPRequest
        request = HTTPRequest(
            url=self.url + endpoint,
            method=method,
            headers=header,
            request_timeout=request_timeout,
            connect_timeout=connect_timeout,
        )
        # Add body if exists
        if body:
            request.body = body

        # Sent HTTPRequest
        response: HTTPResponse = await self.http_client.fetch(request=request)

        for cookie in response.headers.get_list("Set-Cookie"):
            token = header.get("Authorization", None)
            if token and token.startswith("Token "):
                token = token[len("Token ") :]
            else:
                continue
            if cookie.startswith(token):
                self._service_cookie = cookie

        if response_callback:
            response_callback(response)

        if decode_response:
            return json_decode(response.body)
        else:
            return response

    @validate("url")
    def _validate_url(self, proposal):
        url = proposal["value"]
        result: ParseResultBytes = urlparse(url)
        if not all([result.scheme, result.hostname]):
            raise TraitError("Invalid url: at least has to contain scheme and hostname")
        return url

    @staticmethod
    def get_query_string(params: dict) -> str:
        d = {k: v for k, v in params.items() if v is not None}
        query_params: str = urlencode(d, quote_via=quote_plus)
        return "?" + query_params if query_params != "" else ""
