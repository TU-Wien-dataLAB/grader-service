# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import json

from tornado.httpclient import HTTPClientError

from grader_labextension.registry import register_handler
from grader_labextension.handlers.base_handler import ExtensionBaseHandler
from grader_labextension.services.request import RequestService
from tornado.web import HTTPError


@register_handler(
    path=r"\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/submissions\/?"
)
class SubmissionHandler(ExtensionBaseHandler):
    """
    Tornado Handler class for http requests to /lectures/{lecture_id}/assignments/{assignment_id}/submissions.
    """
    async def get(self, lecture_id: int, assignment_id: int):
        """ Sends a GET-request to the grader service and returns submissions of a assignment

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        """
        query_params = RequestService.get_query_string(
            {
                "instructor-version": self.get_argument("instructor-version", None),
                "filter": self.get_argument("filter", "none"),
            }
        )
        try:
            response = await self.request_service.request(
                method="GET",
                endpoint=f"{self.service_base_url}/lectures/{lecture_id}/assignments/{assignment_id}/submissions{query_params}",
                header=self.grader_authentication_header,
            )
        except HTTPClientError as e:
            self.log.error(e.response)
            raise HTTPError(e.code, reason=e.response.reason)
        self.write(json.dumps(response))


@register_handler(
    path=r"\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/submissions\/(?P<submission_id>\d*)\/properties\/?"
)
class SubmissionPropertiesHandler(ExtensionBaseHandler):
    """
    Tornado Handler class for http requests to /lectures/{lecture_id}/assignments/{assignment_id}/submissions/properties.
    """
    async def get(self, lecture_id: int, assignment_id: int, submission_id: int):
        """Sends a GET-request to the grader service and returns the properties of a submission

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        :param submission_id: id of the submission
        :type submission_id: int
        """        

        try:
            response = await self.request_service.request(
                method="GET",
                endpoint=f"{self.service_base_url}/lectures/{lecture_id}/assignments/{assignment_id}/submissions/{submission_id}/properties",
                header=self.grader_authentication_header,
            )
        except HTTPClientError as e:
            self.log.error(e.response)
            raise HTTPError(e.code, reason=e.response.reason)
        self.write(json.dumps(response))

    async def put(self, lecture_id: int, assignment_id: int, submission_id: int):
        """ Sends a PUT-request to the grader service to update the properties of a submission

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        :param submission_id: id of the submission
        :type submission_id: int
        """
        try:
            await self.request_service.request(
                method="PUT",
                endpoint=f"{self.service_base_url}/lectures/{lecture_id}/assignments/{assignment_id}/submissions/{submission_id}/properties",
                header=self.grader_authentication_header,
                body=self.request.body.decode("utf-8"),
                decode_response=False
            )
        except HTTPClientError as e:
            self.log.error(e.response)
            raise HTTPError(e.code, reason=e.response.reason)
        self.write("OK")

@register_handler(
    path=r"\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/submissions\/(?P<submission_id>\d*)\/?"
)
class SubmissionObjectHandler(ExtensionBaseHandler):
    """
    Tornado Handler class for http requests to /lectures/{lecture_id}/assignments/{assignment_id}/submissions/{submission_id}.
    """
    async def get(self, lecture_id: int, assignment_id: int, submission_id: int):
        """Sends a GET-request to the grader service and returns the properties of a submission

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        :param submission_id: id of the submission
        :type submission_id: int
        """        

        try:
            response = await self.request_service.request(
                method="GET",
                endpoint=f"{self.service_base_url}/lectures/{lecture_id}/assignments/{assignment_id}/submissions/{submission_id}",
                header=self.grader_authentication_header,
            )
        except HTTPClientError as e:
            self.log.error(e.response)
            raise HTTPError(e.code, reason=e.response.reason)
        self.write(json.dumps(response))

    async def put(self, lecture_id: int, assignment_id: int, submission_id: int):
        """ Sends a PUT-request to the grader service to update the properties of a submission

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        :param submission_id: id of the submission
        :type submission_id: int
        """
        try:
            await self.request_service.request(
                method="PUT",
                endpoint=f"{self.service_base_url}/lectures/{lecture_id}/assignments/{assignment_id}/submissions/{submission_id}",
                header=self.grader_authentication_header,
                body=self.request.body.decode("utf-8"),
                decode_response=False
            )
        except HTTPClientError as e:
            self.log.error(e.response)
            raise HTTPError(e.code, reason=e.response.reason)
        self.write("OK")
