# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import json
from grader_labextension.registry import register_handler
from grader_labextension.handlers.base_handler import ExtensionBaseHandler
import tornado
from tornado import web
from grader_labextension.services.request import RequestService
from tornado.httpclient import HTTPError


@register_handler(path=r"\/lectures\/?")
class LectureBaseHandler(ExtensionBaseHandler):
    @web.authenticated
    async def get(self):
        """Sends a GET-request to the grader service and returns the autorized lectures
        """
        query_params = RequestService.get_query_string({
            "complete": self.get_argument("complete", None)
        })
        try:
            response = await self.request_service.request(
                "GET",
                f"{self.service_base_url}/lectures{query_params}",
                header=self.grader_authentication_header,
            )
        except HTTPError as e:
            self.set_status(e.code)
            self.write_error(e.code)
            return
        self.write(json.dumps(response))

    @web.authenticated
    async def post(self):
        """Sends a POST-request to the grader service to create a lecture
        """
        data = tornado.escape.json_decode(self.request.body)
        try:
            response = await self.request_service.request(
                "POST",
                f"{self.service_base_url}/lectures",
                body=data,
                header=self.grader_authentication_header,
            )
        except HTTPError as e:
            self.set_status(e.code)
            self.write_error(e.code)
            return
        self.write(json.dumps(response))


@register_handler(path=r"\/lectures\/(?P<lecture_id>\d*)\/?")
class LectureObjectHandler(ExtensionBaseHandler):
    @web.authenticated
    async def put(self, lecture_id: int):
        """Sends a PUT-request to the grader service to update a lecture

        :param lecture_id: id of the lecture
        :type lecture_id: int
        """

        data = tornado.escape.json_decode(self.request.body)
        try:
            response_data: dict = await self.request_service.request(
                "PUT",
                f"{self.service_base_url}/lectures/{lecture_id}",
                body=data,
                header=self.grader_authentication_header,
            )
        except HTTPError as e:
            self.set_status(e.code)
            self.write_error(e.code)
            return
        self.write(json.dumps(response_data))

    @web.authenticated
    async def get(self, lecture_id: int):
        """Sends a GET-request to the grader service and returns the lecture

        :param lecture_id: id of the lecture
        :type lecture_id: int
        """
        try:
            response_data: dict = await self.request_service.request(
                "GET",
                f"{self.service_base_url}/lectures/{lecture_id}",
                header=self.grader_authentication_header,
            )
        except HTTPError as e:
            self.set_status(e.code)
            self.write_error(e.code)
            return
        self.write(json.dumps(response_data))

    @web.authenticated
    async def delete(self, lecture_id: int):
        """Sends a DELETE-request to the grader service to delete a lecture

        :param lecture_id: id of the lecture
        :type lecture_id: int
        """

        try:
            await self.request_service.request(
                "DELETE",
                f"{self.service_base_url}/lectures/{lecture_id}",
                header=self.grader_authentication_header,
            )
        except HTTPError as e:
            self.set_status(e.code)
            self.write_error(e.code)
            return
        self.write("OK")


@register_handler(
    path=r"\/lectures\/(?P<lecture_id>\d*)\/users\/?"
)
class LectureStudentsHandler(ExtensionBaseHandler):
    async def get(self, lecture_id: int):
        try:
            response = await self.request_service.request(
                method="GET",
                endpoint=f"{self.service_base_url}/lectures/{lecture_id}/users/",
                header=self.grader_authentication_header,
            )
        except HTTPError as e:
            self.set_status(e.code)
            self.write_error(e.code)
            return

        self.write(json.dumps(response))