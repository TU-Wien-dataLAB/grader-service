# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import json
import socket
from typing import Dict, Union
from urllib.parse import quote_plus, urlencode

from tornado.escape import json_decode
from tornado.httpclient import AsyncHTTPClient, HTTPResponse
from traitlets.config.configurable import LoggingConfigurable
from traitlets.traitlets import Int, TraitError, Unicode, validate


class RequestService(LoggingConfigurable):
    def __init__(self, url: str, **kwargs):
        super().__init__(**kwargs)
        self.http_client = AsyncHTTPClient()
        self.url = url

    async def request(
        self,
        method: str,
        endpoint: str,
        body: dict = None,
        header: Dict[str, str] = None,
    ) -> Union[dict, list]:
        if body:
            response: HTTPResponse = await self.http_client.fetch(
                self.url + endpoint,
                method=method,
                headers=header,
                body=json.dumps(body),
            )
        else:
            response: HTTPResponse = await self.http_client.fetch(
                self.url + endpoint, method=method, headers=header, body=body
            )
        return json_decode(response.body)

    @validate("scheme")
    def _validate_scheme(self, proposal):
        if proposal["value"] not in {"http", "https"}:
            raise TraitError("Invalid scheme. Use either http or https")
        return proposal["value"]

    @validate("host")
    def _validate_host(self, proposal):
        try:
            socket.gethostbyname(proposal["value"])
            return proposal["value"]
        except socket.error:
            raise TraitError(
                "Host adress has to resolve. Invalid hostname %s" % proposal["value"]
            )

    @validate("port")
    def _validate_port(self, proposal):
        value = proposal["value"]
        if not 1 <= value <= 65535:
            raise TraitError("Port number has to be between 1 and 65535.")
        return value

    @staticmethod
    def get_query_string(params: dict) -> dict:
        d = {k: v for k, v in params.items() if v is not None}
        query_params: str = urlencode(d, quote_via=quote_plus)
        return "?" + query_params if query_params != "" else ""
