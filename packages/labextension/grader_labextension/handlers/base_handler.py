# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
import functools
import os
from typing import Awaitable, Optional

from grader_service.handlers.base_handler import GraderErrorMixin
from jupyter_server.base.handlers import APIHandler
from tornado.httpclient import HTTPError, HTTPResponse
from traitlets.config.configurable import SingletonConfigurable
from traitlets.traitlets import Unicode

from grader_labextension.services.request import RequestService, RequestServiceError


def cache(max_age: int):
    if max_age < 0:
        raise ValueError("max_age must be larger than 0!")

    def wrapper(handler_method):
        @functools.wraps(handler_method)
        async def request_handler_wrapper(self: "ExtensionBaseHandler", *args, **kwargs):
            self.set_header("Cache-Control", f"max-age={max_age}, must-revalidate, private")
            return await handler_method(self, *args, **kwargs)

        return request_handler_wrapper

    return wrapper


class HandlerConfig(SingletonConfigurable):
    hub_api_url = Unicode(
        os.environ.get("JUPYTERHUB_API_URL"), help="The url of the hubs api."
    ).tag(config=True)
    hub_api_token = Unicode(
        os.environ.get("JUPYTERHUB_API_TOKEN"), help="The authorization token to access the hub api"
    ).tag(config=True)
    hub_user = Unicode(os.environ.get("JUPYTERHUB_USER"), help="The user name in jupyter hub.").tag(
        config=True
    )
    grader_api_token = Unicode(
        os.environ.get("GRADER_API_TOKEN"),
        help="The authorization token to access the grader service api",
    ).tag(config=True)
    service_base_url = Unicode(
        os.environ.get("GRADER_BASE_URL", "/services/grader/"),
        help="Base URL to use for each request to the grader service",
    ).tag(config=True)
    lectures_base_path = Unicode(
        "lectures",
        help="The path in each user home directory where lecture directories are created.",
    ).tag(config=True)


class ExtensionBaseHandler(GraderErrorMixin, APIHandler):
    """
    BaseHandler for all server-extension handler
    """

    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass

    def set_service_headers(self, response: HTTPResponse):
        for header in response.headers.get_list("Cache-Control"):
            self.set_header("Cache-Control", header)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.root_dir = os.path.expanduser(
            os.path.join(
                self.settings["server_root_dir"], HandlerConfig.instance().lectures_base_path
            )
        ).rstrip("/")
        # Lazily initialize RequestService to ensure network is ready
        self._request_service = None

    @property
    def request_service(self):
        if self._request_service is None:
            self._request_service = RequestService.instance()
        return self._request_service

    @property
    def service_base_url(self):
        return HandlerConfig.instance().service_base_url

    @property
    def grader_authentication_header(self):
        """Returns the authentication header

        :return: authentication header
        :rtype: dict
        """

        return dict(Authorization="Token " + HandlerConfig.instance().grader_api_token)

    @property
    def user_name(self):
        return self.current_user.name

    async def get_lecture(self, lecture_id: int) -> dict:
        try:
            lecture = await self.request_service.request(
                "GET",
                f"{self.service_base_url}api/lectures/{lecture_id}",
                header=self.grader_authentication_header,
            )
            return lecture
        except RequestServiceError as e:
            self.log.error(e)
            raise HTTPError(e.code, reason=e.message)

    async def get_assignment(self, lecture_id: int, assignment_id: int) -> dict:
        try:
            assignment = await self.request_service.request(
                "GET",
                f"{self.service_base_url}api/lectures/{lecture_id}/assignments/{assignment_id}",
                header=self.grader_authentication_header,
            )
            return assignment
        except RequestServiceError as e:
            self.log.error(e)
            raise HTTPError(e.code, reason=e.message)
