# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import json
import os
import urllib.parse

import tornado
from tornado.web import HTTPError, authenticated

from grader_labextension.handlers.base_handler import ExtensionBaseHandler
from grader_labextension.registry import register_handler
from grader_labextension.services.request import RequestService, RequestServiceError


@register_handler(path=r"api\/lectures\/?")
class LectureBaseHandler(ExtensionBaseHandler):
    """
    Tornado Handler class for http requests to /lectures.
    """

    @authenticated
    async def get(self):
        """Sends a GET-request to the grader service and returns the autorized lectures"""
        query_params = RequestService.get_query_string(
            {
                "complete": self.get_argument("complete", None),
                "instructor": self.get_argument("instructor", None),
            }
        )
        try:
            response = await self.request_service.request(
                "GET",
                f"{self.service_base_url}api/lectures{query_params}",
                header=self.grader_authentication_header,
                response_callback=self.set_service_headers,
            )
        except RequestServiceError as e:
            self.log.error(e)
            raise HTTPError(e.code, reason=e.message)
        self.write(json.dumps(response))

    @authenticated
    async def post(self):
        """Sends a POST-request to the grader service to create a lecture"""
        data = tornado.escape.json_decode(self.request.body)
        try:
            response = await self.request_service.request(
                "POST",
                f"{self.service_base_url}api/lectures",
                body=data,
                header=self.grader_authentication_header,
            )
        except RequestServiceError as e:
            self.log.error(e)
            raise HTTPError(e.code, reason=e.message)
        self.write(json.dumps(response))


@register_handler(path=r"api\/lectures\/(?P<lecture_id>\d*)\/?")
class LectureObjectHandler(ExtensionBaseHandler):
    """
    Tornado Handler class for http requests to /lectures/{lecture_id}.
    """

    @authenticated
    async def put(self, lecture_id: int):
        """Sends a PUT-request to the grader service to update a lecture

        :param lecture_id: id of the lecture
        :type lecture_id: int
        """

        data = tornado.escape.json_decode(self.request.body)
        try:
            response_data: dict = await self.request_service.request(
                "PUT",
                f"{self.service_base_url}api/lectures/{lecture_id}",
                body=data,
                header=self.grader_authentication_header,
            )
        except RequestServiceError as e:
            self.log.error(e)
            raise HTTPError(e.code, reason=e.message)
        self.write(json.dumps(response_data))

    @authenticated
    async def get(self, lecture_id: int):
        """Sends a GET-request to the grader service and returns the lecture

        :param lecture_id: id of the lecture
        :type lecture_id: int
        """
        try:
            response_data: dict = await self.request_service.request(
                "GET",
                f"{self.service_base_url}api/lectures/{lecture_id}",
                header=self.grader_authentication_header,
                response_callback=self.set_service_headers,
            )
        except RequestServiceError as e:
            self.log.error(e)
            raise HTTPError(e.code, reason=e.message)
        self.write(json.dumps(response_data))

    @authenticated
    async def delete(self, lecture_id: int):
        """Sends a DELETE-request to the grader service to delete a lecture

        :param lecture_id: id of the lecture
        :type lecture_id: int
        """

        try:
            await self.request_service.request(
                "DELETE",
                f"{self.service_base_url}api/lectures/{lecture_id}",
                header=self.grader_authentication_header,
            )
        except RequestServiceError as e:
            self.log.error(e)
            raise HTTPError(e.code, reason=e.message)
        self.write({"status": "OK"})


@register_handler(path=r"api\/lectures\/(?P<lecture_id>\d*)\/users\/?")
class LectureStudentsHandler(ExtensionBaseHandler):
    """
    Tornado Handler class for http requests to /lectures/{lecture_id}/users.
    """

    @authenticated
    async def get(self, lecture_id: int):
        """
        Sends a GET request to the grader service and returns attendants of lecture
        :param lecture_id: id of the lecture
        :return: attendants of lecture
        """
        try:
            response = await self.request_service.request(
                method="GET",
                endpoint=f"{self.service_base_url}api/lectures/{lecture_id}/users",
                header=self.grader_authentication_header,
                response_callback=self.set_service_headers,
            )
        except RequestServiceError as e:
            self.log.error(e)
            raise HTTPError(e.code, reason=e.message)

        self.write(json.dumps(response))


def get_content_type_from_response(response):
    """
    Extract Content-Type from raw response string containing headers.
    """
    lines = response.split("\n")  # Split the response into lines
    for line in lines:
        if "Content-Type" in line:  # Look for the Content-Type header
            key, value = line.split(":", 1)  # Split key and value
            return value.strip()  # Return the Content-Type value, stripped of whitespace
    return ""  # Default if Content-Type is not found


@register_handler(path=r"api\/lectures\/(?P<lecture_id>\d*)\/submissions\/?")
class SubmissionLectureHandler(ExtensionBaseHandler):
    """ "
    Tornado Handler class for http requests to /lectures/{lecture_id}/submissions
    """

    @authenticated
    async def get(self, lecture_id: int):
        """Return the submissions of a specific lecture.

        Two query parameter:
        1 - filter
        latest: only get the latest submissions of users.
        best: only get the best submissions by score of users.

        2 - format:
        csv: return list as comma separated values
        json: return list as JSON

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :raises HTTPError: throws err if user is not authorized or
        the assignment was not found
        """
        query_params = RequestService.get_query_string(
            {
                "filter": self.get_argument("filter", "best"),
                "format": self.get_argument("format", "json"),
            }
        )
        try:
            response = await self.request_service.request(
                "GET",
                f"{self.service_base_url}api/lectures/{lecture_id}/submissions{query_params}",
                header=self.grader_authentication_header,
                response_callback=self.set_service_headers,
            )

        except RequestServiceError as e:
            self.log.error(e)
            raise HTTPError(e.code, reason=e.message)

        lecture = await self.get_lecture(lecture_id)
        dir_path = os.path.join(self.root_dir, lecture["code"])
        os.makedirs(dir_path, exist_ok=True)

        parsed_query_params = urllib.parse.parse_qs(query_params.lstrip("?"))
        filter_value = parsed_query_params.get("filter", ["none"])[0]
        format_value = parsed_query_params.get("format", ["json"])[0]

        file_path = os.path.join(
            dir_path, f"{lecture['name']}_{filter_value}_submissions.{format_value}"
        )
        if format_value == "csv":
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(response)
        elif format_value == "json":
            json_content = (
                json.dumps(response, indent=2) if isinstance(response, dict) else response
            )
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(json_content)
        else:
            raise HTTPError(400, reason="Invalid format specified")
        self.write(
            {
                "status": "OK",
                "message": f"File saved successfully: {file_path}",
                "file_path": file_path,
            }
        )
