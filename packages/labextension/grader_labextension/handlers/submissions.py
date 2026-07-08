# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import json

from grader_service.errors import APIError
from tornado.web import HTTPError, authenticated

from grader_labextension.handlers.base_handler import ExtensionBaseHandler
from grader_labextension.registry import register_handler
from grader_labextension.services.request import RequestService, RequestServiceError


@register_handler(
    path=r"api\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/submissions\/?"
)
class SubmissionHandler(ExtensionBaseHandler):
    """
    Tornado Handler class for http requests to /lectures/{lecture_id}/assignments/{assignment_id}/submissions.
    """

    @authenticated
    async def get(self, lecture_id: int, assignment_id: int):
        """Sends a GET-request to the grader service and returns submissions of an assignment

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
                endpoint=f"{self.service_base_url}api/lectures/{lecture_id}/assignments/{assignment_id}/submissions{query_params}",
                header=self.grader_authentication_header,
                response_callback=self.set_service_headers,
            )
        except RequestServiceError as e:
            self.log.error(e)
            raise HTTPError(e.code, reason=e.message)
        self.write(json.dumps(response))


@register_handler(
    path=r"api\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/submissions\/"
    r"(?P<submission_id>\d*)\/logs\/?"
)
class SubmissionLogsHandler(ExtensionBaseHandler):
    @authenticated
    async def get(self, lecture_id: int, assignment_id: int, submission_id: int):
        """Sends a GET-request to the grader service and returns the logs of a submission

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
                endpoint=f"{self.service_base_url}api/lectures/{lecture_id}/assignments/"
                f"{assignment_id}/submissions/{submission_id}/logs",
                header=self.grader_authentication_header,
                response_callback=self.set_service_headers,
            )
            self.log.info(response)
        except RequestServiceError as e:
            self.log.error(e)
            raise HTTPError(e.code, reason=e.message)
        self.write(response)


@register_handler(
    path=r"api\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/submissions\/"
    r"(?P<submission_id>\d*)\/properties\/?"
)
class SubmissionPropertiesHandler(ExtensionBaseHandler):
    """
    Tornado Handler class for http requests to
    /lectures/{lecture_id}/assignments/{assignment_id}/submissions/properties.
    """

    @authenticated
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
                endpoint=f"{self.service_base_url}api/lectures/{lecture_id}/assignments/"
                f"{assignment_id}/submissions/{submission_id}/properties",
                header=self.grader_authentication_header,
                response_callback=self.set_service_headers,
            )
        except RequestServiceError as e:
            self.log.error(e)
            raise HTTPError(e.code, reason=e.message)
        self.write(response)

    async def put(self, lecture_id: int, assignment_id: int, submission_id: int):
        """Sends a PUT-request to the grader service to update the properties of a submission

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
                endpoint=f"{self.service_base_url}api/lectures/{lecture_id}/assignments/"
                f"{assignment_id}/submissions/{submission_id}/properties",
                header=self.grader_authentication_header,
                body=self.request.body.decode("utf-8"),
                decode_response=False,
                request_timeout=300.0,
            )
        except RequestServiceError as e:
            self.log.error(e)
            raise HTTPError(e.code, reason=e.message)
        self.write({"status": "OK"})


@register_handler(
    path=r"api\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/submissions\/"
    r"(?P<submission_id>\d*)\/edit\/?"
)
class SubmissionEditHandler(ExtensionBaseHandler):
    async def put(self, lecture_id: int, assignment_id: int, submission_id: int):
        """Sends a PUT-request to the grader service to create or override an edit repository of the submission

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        :param submission_id: id of the submission
        :type submission_id: int
        """
        try:
            response = await self.request_service.request(
                method="PUT",
                endpoint=f"{self.service_base_url}api/lectures/{lecture_id}/assignments/"
                f"{assignment_id}/submissions/{submission_id}/edit",
                header=self.grader_authentication_header,
                body=self.request.body.decode("utf-8"),
                request_timeout=300.0,
                connect_timeout=300.0,
            )
        except RequestServiceError as e:
            self.log.error(e)
            raise HTTPError(e.code, reason=e.message)
        self.write(json.dumps(response))


@register_handler(
    path=r"api\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/submissions\/"
    r"(?P<submission_id>\d*)\/?"
)
class SubmissionObjectHandler(ExtensionBaseHandler):
    """
    Tornado Handler class for http requests to
    /lectures/{lecture_id}/assignments/{assignment_id}/submissions/{submission_id}.
    """

    @authenticated
    async def get(self, lecture_id: int, assignment_id: int, submission_id: int):
        """Sends a GET-request to the grader service and returns a submission

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
                endpoint=f"{self.service_base_url}api/lectures/{lecture_id}/assignments/"
                f"{assignment_id}/submissions/{submission_id}",
                header=self.grader_authentication_header,
                response_callback=self.set_service_headers,
            )
        except RequestServiceError as e:
            self.log.error(e)
            raise HTTPError(e.code, reason=e.message)
        self.write(json.dumps(response))

    async def put(self, lecture_id: int, assignment_id: int, submission_id: int):
        """Sends a PUT-request to the grader service to update a submission

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
                endpoint=f"{self.service_base_url}api/lectures/{lecture_id}/assignments/"
                f"{assignment_id}/submissions/{submission_id}",
                header=self.grader_authentication_header,
                body=self.request.body.decode("utf-8"),
                decode_response=False,
            )
        except RequestServiceError as e:
            self.log.error(e)
            raise HTTPError(e.code, reason=e.message)
        self.write({"status": "OK"})

    async def delete(self, lecture_id: int, assignment_id: int, submission_id: int):
        """Sends a DELETE-request to the grader service to "soft"-delete an assignment

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        :param submission_id: id of the submission
        :type submission_id: int
        """

        try:
            await self.request_service.request(
                method="DELETE",
                endpoint=f"{self.service_base_url}api/lectures/{lecture_id}/assignments/"
                f"{assignment_id}/submissions/{submission_id}",
                header=self.grader_authentication_header,
                decode_response=False,
            )
        except RequestServiceError as e:
            raise HTTPError(e.code, reason=e.message)

        self.write({"status": "OK"})


@register_handler(
    path=r"api\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/"
    r"submissions\/lti\/?"
)
class LtiSyncHandler(ExtensionBaseHandler):
    def raise_status(self, request):
        try:
            request.raise_for_status()
            request = request.json()
        except Exception:
            self.log.error(request["message"])
            raise HTTPError(request["status"], reason=request["message"])
        return request

    async def put(self, lecture_id: int, assignment_id: int):
        query_params = RequestService.get_query_string(
            {"option": self.get_argument("option", "selection")}
        )
        try:
            response = await self.request_service.request(
                method="PUT",
                endpoint=f"{self.service_base_url}api/lectures/{lecture_id}/assignments/"
                f"{assignment_id}/submissions/lti/{query_params}",
                header=self.grader_authentication_header,
                body=self.request.body.decode("utf-8"),
            )
        except RequestServiceError as e:
            self.log.error(e)
            raise APIError(e.code, message=e.message)

        self.write(json.dumps(response))


@register_handler(
    path=r"api\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/"
    r"submissions\/count\/?"
)
class SubmissionCountHandler(ExtensionBaseHandler):
    """
    Tornado Handler class for http requests to
    /lectures/{lecture_id}/assignments/{assignment_id}/submissions/count.
    """

    @authenticated
    async def get(self, lecture_id: int, assignment_id: int):
        """Returns the count of submissions made by the student for an assignment.

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        """

        try:
            response = await self.request_service.request(
                method="GET",
                endpoint=f"{self.service_base_url}api/lectures/{lecture_id}/assignments/"
                f"{assignment_id}/submissions/count",
                header=self.grader_authentication_header,
                response_callback=self.set_service_headers,
            )
            self.log.info(f"{response}")
        except RequestServiceError as e:
            self.log.error(e)
            raise HTTPError(e.code, reason=e.message)
        self.write(json.dumps(response))
