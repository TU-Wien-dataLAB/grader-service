# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import logging, json

from tornado.httpclient import AsyncHTTPClient, HTTPResponse
from traitlets.config.configurable import LoggingConfigurable, SingletonConfigurable
from typing import Dict, Union, Callable, Optional
from tornado.escape import json_decode
from traitlets.traitlets import Int, TraitError, Unicode, validate
from urllib.parse import urlencode, quote_plus, urlparse, ParseResultBytes
import os


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
        response_callback: Optional[Callable[[HTTPResponse], None]] = None
    ) -> Union[dict, list, HTTPResponse]:
        self.log.info(self.url + endpoint)
        if self._service_cookie:
            header["Cookie"] = self._service_cookie
        if body:
            if isinstance(body, dict):
                body = json.dumps(body)
            response: HTTPResponse = await self.http_client.fetch(
                self.url + endpoint,
                method=method,
                headers=header,
                body=body,
            )
        else:
            response: HTTPResponse = await self.http_client.fetch(
                self.url + endpoint, method=method, headers=header, body=body
            )
        for cookie in response.headers.get_list("Set-Cookie"):
            token = header.get("Authorization", None)
            if token and token.startswith("Token "):
                token = token[len("Token "):]
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
