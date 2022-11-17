# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import json
import datetime
from http import HTTPStatus

import requests
from tornado.httpclient import HTTPClientError
from urllib.parse import urlparse, urlunparse

from grader_labextension.registry import register_handler
from grader_labextension.handlers.base_handler import ExtensionBaseHandler, cache, HandlerConfig
from grader_labextension.services.request import RequestService
from tornado.web import HTTPError


@register_handler(
    path=r"\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/submissions\/?"
)
class SubmissionHandler(ExtensionBaseHandler):
    """
    Tornado Handler class for http requests to /lectures/{lecture_id}/assignments/{assignment_id}/submissions.
    """

    @cache(max_age=15)
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
                response_callback=self.set_service_headers
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
                response_callback=self.set_service_headers
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

    @cache(max_age=15)
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
                endpoint=f"{self.service_base_url}/lectures/{lecture_id}/assignments/{assignment_id}/submissions/{submission_id}",
                header=self.grader_authentication_header,
                response_callback=self.set_service_headers
            )
        except HTTPClientError as e:
            self.log.error(e.response)
            raise HTTPError(e.code, reason=e.response.reason)
        self.write(json.dumps(response))

    async def put(self, lecture_id: int, assignment_id: int, submission_id: int):
        """ Sends a PUT-request to the grader service to update the a submission

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


def build_grade_publish_body(uid: str, score: float, max_score: float):
    return {
        "timestamp": str(datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()),
        "scoreGiven": score,
        "comment": "Automatically synced",
        "scoreMaximum": max_score,
        "activityProgress": "Submitted",
        "gradingProgress": "FullyGraded",
        "userId": uid
    }


@register_handler(
    path=r"\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/submissions\/lti\/?"
)
class LtiSyncHandler(ExtensionBaseHandler):

    def raise_status(self, request):
        try:
            request.raise_for_status()
            request = request.json()
        except Exception as e:
            self.log.error(request["message"])
            raise HTTPError(request["status"], reason=request["message"])
        return request

    async def put(self, lecture_id: int, assignment_id: int):
        # get submissions with score and lti customized username
        try:
            scores = await self.request_service.request(
                method="GET",
                endpoint=f"{self.service_base_url}/lectures/{lecture_id}/assignments/{assignment_id}/submissions/lti",
                header=self.grader_authentication_header)
        except HTTPClientError as e:
            self.log.error(e.response)
            raise HTTPError(e.code, reason=e.response.reason)

        grades = []

        # Get lineitems URL
        instructor = requests.get(HandlerConfig.instance().hub_api_url + "/users/" + self.user_name,
                                  headers={"Authorization": "token " + HandlerConfig.instance().hub_api_token})

        instructor = self.raise_status(instructor)
        if instructor["auth_state"] is None:
            raise HTTPError(HTTPStatus.NOT_FOUND, "Auth state of current user could not be found! Please logout and "
                                                  "login again and check if enable_auth_state is enabled in JupyterHub!")

        lineitems_url = instructor["auth_state"]["course_lineitems"]
        if lineitems_url is None:
            raise HTTPError(HTTPStatus.NOT_FOUND,
                            "Lineitems URL could not be found! Do you use the LTI13Authenticator?")
        membership_url = instructor["auth_state"]["membership_url"]
        members = requests.get(membership_url, headers={"Authorization": "Bearer " + scores["token"],
                                                        "Accept": "application/vnd.ims.lti-nrps.v2"
                                                                  ".membershipcontainer+json"})

        members = self.raise_status(members)

        # match username with lti sourced id
        syncable_user_count = 0
        for score in scores["scores"]:
            for member in members["members"]:
                if member["lis_person_sourcedid"] == score["username"]:
                    syncable_user_count += 1
                    grades.append(build_grade_publish_body(member["user_id"], score["score"],
                                                           scores["assignment"]["points"]))

        # get lineitem if not found, create new lineitem
        assignment = scores["assignment"]

        lineitems = requests.get(lineitems_url,
                                 headers={"Authorization": "Bearer " + scores["token"],
                                          "Accept": "application/vnd.ims.lis.v2.lineitemcontainer+json"})

        lineitems = self.raise_status(lineitems)
        lineitem = None
        for item in lineitems:
            if item["label"] == assignment["name"]:
                # lineitem found
                lineitem = item
                break

        # create lineitem
        if lineitem is None:
            lineitem_body = {"scoreMaximum": int(assignment["points"]), "label": assignment["name"],
                             "resourceId": assignment["id"],
                             "tag": "grade", "startDateTime": str(datetime.datetime.now()),
                             "endDateTime": str(datetime.date.today() + datetime.timedelta(days=1, hours=1))}

            lineitem = requests.post(lineitems_url, json=lineitem_body,
                                     headers={"Authorization": "Bearer " + scores["token"],
                                              "Content-Type": "application/vnd.ims.lis.v2.lineitem+json"})
            lineitem = self.raise_status(lineitem)

        # add scores endpoint to lineitem url
        url_parsed = urlparse(lineitem["id"])
        lineitem = url_parsed._replace(path=url_parsed.path + "/scores").geturl()

        # send score to learning tool
        synced_user = 0
        for grade in grades:
            response = requests.post(lineitem, json=grade,
                                     headers={"Authorization": "Bearer " + scores["token"],
                                              "Content-Type": "application/vnd.ims.lis.v1.score+json"})
            if response.ok:
                synced_user += 1

        self.write({"syncable_users": syncable_user_count, "synced_user": synced_user})
