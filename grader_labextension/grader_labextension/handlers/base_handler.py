# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
import json
import traceback
from typing import Optional, Awaitable

from tornado import httputil
from tornado.web import HTTPError

from grader_labextension.api.models.error_message import ErrorMessage
from grader_labextension.services.request import RequestService
from jupyter_server.base.handlers import APIHandler
import os
from tornado.httpclient import HTTPClient, HTTPClientError
from traitlets.config.configurable import SingletonConfigurable
from traitlets.traitlets import Unicode

# test_token: ebce9dfa2a694fb9bb06883bd8bb6012

class HandlerConfig(SingletonConfigurable):
    hub_api_url = Unicode(os.environ.get("JUPYTERHUB_API_URL"), help="The url of the hubs api.").tag(config=True)
    hub_api_token = Unicode(os.environ.get("JUPYTERHUB_API_TOKEN"), help="The authorization token to access the hub api").tag(config=True)
    hub_user = Unicode(os.environ.get("JUPYTERHUB_USER"), help="The user name in jupyter hub.").tag(config=True)
    service_base_url = Unicode(
        os.environ.get("GRADER_BASE_URL", "/services/grader"),
        help="Base URL to use for each request to the grader service",
    ).tag(config=True)


class ExtensionBaseHandler(APIHandler):
    """
    BaseHandler for all server-extension handler
    """

    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass

    request_service = RequestService()
    http_client = HTTPClient()
    # base_url = "/services/grader"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, *kwargs)
        self.root_dir = os.path.expanduser(self.settings["server_root_dir"])

    @property
    def service_base_url(self):
        return HandlerConfig.instance().service_base_url

    @property
    def grader_authentication_header(self):
        """Returns the authentication header

        :return: authentication header
        :rtype: dict
        """

        return dict(Authorization="Token " + HandlerConfig.instance().hub_api_token)

    async def get_lecture(self, lecture_id) -> dict:
        try:
            lecture = await self.request_service.request(
                "GET",
                f"{self.service_base_url}/lectures/{lecture_id}",
                header=self.grader_authentication_header,
            )
            return lecture
        except HTTPClientError as e:
            self.log.error(e.response)
            raise HTTPError(e.code, reason=e.response.reason)

    async def get_assignment(self, lecture_id, assignment_id):
        try:
            assignment = await self.request_service.request(
                "GET",
                f"{self.service_base_url}/lectures/{lecture_id}/assignments/{assignment_id}",
                header=self.grader_authentication_header,
            )
            return assignment
        except HTTPClientError as e:
            self.log.error(e.response)
            raise HTTPError(e.code, reason=e.response.reason)

    def write_error(self, status_code: int, **kwargs) -> None:
        self.set_header('Content-Type', 'application/json')
        _, e, _ = kwargs.get("exc_info", (None, None, None))
        error = httputil.responses.get(status_code, "Unknown")
        reason = None
        if e and isinstance(e, HTTPError) and e.reason:
            reason = e.reason
        if self.settings.get("serve_traceback") and "exc_info" in kwargs:
            # in debug mode, try to send a traceback
            lines = []
            for line in traceback.format_exception(*kwargs["exc_info"]):
                lines.append(line)
            self.finish(json.dumps(
                ErrorMessage(status_code, error, self.request.path, reason, traceback=json.dumps(lines)).to_dict()))
        else:
            self.finish(json.dumps(ErrorMessage(status_code, error, self.request.path, reason).to_dict()))
