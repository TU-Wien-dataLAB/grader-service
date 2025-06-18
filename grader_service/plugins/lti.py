import datetime
import json
import os
import time
from http import HTTPStatus
from urllib.parse import urlparse

import jwt
from tornado.escape import json_decode, url_escape
from tornado.httpclient import AsyncHTTPClient, HTTPClientError, HTTPRequest
from tornado.web import HTTPError
from traitlets import Bool, Callable, Unicode, Union
from traitlets.config import SingletonConfigurable


def default_lti_username_match(member, submission, log) -> bool:
    return False


def default_enable_lti(lecture, assignment, submissions):
    return False


def default_enable_sync_on_feedback(lecture, assignment, submissions):
    return False


class LTISyncGrades(SingletonConfigurable):
    enabled = Union(
        [Bool(False), Callable(default_enable_lti)],
        allow_none=True,
        config=True,
        help="""
        Determines if the LTI Sync Grades plugin should be used, defaults to False.
        Is either a bool value or
        a function with the params (lecture, assignment, submissions) returning a bool.
        """,
    )

    sync_on_feedback = Union(
        [Bool(False), Callable(default_enable_sync_on_feedback)],
        allow_none=True,
        config=True,
        help="""
        Determines if submissions should be automatically synchronised, on feedback generation, defaults to False.
        Only synchronises scores when LTISyncGrades.enabled is True.
        Is either a bool value or
        a function with the params (lecture, assignment, submissions) returning a bool.
        """,
    )
    client_id = Unicode(None, config=True, allow_none=True)
    token_url = Unicode(None, config=True, allow_none=True)
    username_match = Callable(
        default_value=default_lti_username_match,
        config=True,
        allow_none=True,
        help="Function used to match lti member object with submission object to. Is given member, submission object and log as params and returns boolean if it is the users submission",
    )

    token_private_key = Union(
        [Unicode(os.environ.get("LTI_PRIVATE_KEY", None)), Callable(None)],
        allow_none=True,
        config=True,
        help="""
        Private Key used to encrypt bearer token request
        """,
    )
    resolve_lti_urls = Callable(
        default_value=None,
        config=True,
        allow_none=True,
        help="Returns membership and lineitem URL needed for grade sync",
    )

    # cache for lti token
    cache_token = {"token": None, "ttl": datetime.datetime.now()}

    def check_if_lti_enabled(self, lecture, assignment, submissions, feedback_sync):
        if callable(self.enabled):
            enable_lti = self.enabled(lecture, assignment, submissions)
        else:
            enable_lti = self.enabled

        if enable_lti:
            if feedback_sync:
                if self.sync_on_feedback:
                    return True
                else:
                    return False
            else:
                return True
        else:
            return False

    async def start(self, lecture, assignment, submissions):
        self.log.info("LTI: start grade sync")
        if len(submissions) == 0:
            raise HTTPError(HTTPStatus.BAD_REQUEST, reason="No submissions to sync")

        # 1. request bearer token
        self.log.debug("LTI: request bearer token")
        stamp = datetime.datetime.now()
        if self.cache_token["token"] and self.cache_token["ttl"] > stamp - datetime.timedelta(
            minutes=50
        ):
            token = self.cache_token["token"]
        else:
            token = await self.request_bearer_token()
            self.cache_token["token"] = token
            self.cache_token["ttl"] = datetime.datetime.now()

        # 2. resolve lti urls
        self.log.debug("LTI: resolve lti url")
        try:
            lti_urls = self.resolve_lti_urls(lecture, assignment, submissions)
            self.log.debug(f"LTI membership and lineitems URL: {lti_urls}")
            lineitems_url = lti_urls["lineitems_url"]
            membership_url = lti_urls["membership_url"]
        except Exception as e:
            self.log.error(e)
            raise e
        # 3. get all members
        self.log.debug("LTI: request all members of lti course")
        httpclient = AsyncHTTPClient()
        try:
            response = await httpclient.fetch(
                HTTPRequest(
                    url=membership_url,
                    method="GET",
                    headers={
                        "Authorization": "Bearer " + self.cache_token["token"],
                        "Accept": "application/vnd.ims.lti-nrps.v2.membershipcontainer+json",
                    },
                )
            )
        except HTTPClientError as e:
            self.log.error(e.response)
            raise HTTPError(e.code, reason="Unable to get users of course:" + e.response.reason)
        members = json_decode(response.body)["members"]

        # 4. match usernames of submissions to lti memberships
        # and generate for each submission a request body -> grades list
        self.log.debug("LTI: match grader usernames with lti identifier")
        grades = []
        syncable_user_count = 0
        for submission in submissions:
            for member in members:
                if self.username_match(member, submission, self.log):
                    syncable_user_count += 1
                    grades.append(
                        self.build_grade_publish_body(
                            member["user_id"], submission["score"], float(assignment["points"])
                        )
                    )
        self.log.info(f"LTI: matched {syncable_user_count} users")
        # 6. get all lineitems
        self.log.debug("LTI: resolve lti url")
        try:
            response = await httpclient.fetch(
                HTTPRequest(
                    url=lineitems_url,
                    method="GET",
                    headers={
                        "Authorization": "Bearer " + self.cache_token["token"],
                        "Accept": "application/vnd.ims.lis.v2.lineitemcontainer+json",
                    },
                )
            )
        except HTTPClientError as e:
            self.log.error(e.response)
            raise HTTPError(e.code, reason="Unable to get lineitems of course:" + e.response.reason)
        lineitems = json_decode(response.body)
        self.log.debug(f"LTI found lineitems: {lineitems}")

        # 7. check if a lineitem with assignment name exists
        lineitem = None
        for item in lineitems:
            if item["label"] == assignment["name"]:
                # lineitem found
                self.log.debug(f"LTI found lineitem: {item}")
                lineitem = item
                break

        # 8. if does not exist, create a lineitem with the assignment name
        if lineitem is None:
            lineitem_body = {
                "scoreMaximum": float(assignment["points"]),
                "label": assignment["name"],
                "resourceId": assignment["id"],
                "tag": "grade",
                "startDateTime": str(datetime.datetime.now()),
                "endDateTime": str(datetime.date.today() + datetime.timedelta(days=1, hours=1)),
            }
            try:
                response = await httpclient.fetch(
                    HTTPRequest(
                        url=lineitems_url,
                        method="POST",
                        body=json.dumps(lineitem_body),
                        headers={
                            "Authorization": "Bearer " + self.cache_token["token"],
                            "Content-Type": "application/vnd.ims.lis.v2.lineitem+json",
                        },
                    )
                )
            except HTTPClientError as e:
                self.log.error(e.response)
                raise HTTPError(
                    e.code, reason="Unable to create new lineitem in course:" + e.response.reason
                )
            # due to different "interpretations" of the ims lti standard,
            # the response is sometimes a list containing the lineitem or
            # just the lineitem json
            try:
                lineitem_response = json_decode(response.body)
            except Exception as e:
                self.log.error("LTI: could not decode lineitem request response")
                raise e
            if isinstance(lineitem_response, list):
                lineitem = lineitem_response[0]
            elif isinstance(lineitem_response, dict):
                lineitem = lineitem_response
            else:
                self.log.error("LTI: lineitem request response does not match dict or list")
                raise HTTPError(
                    HTTPStatus.UNPROCESSABLE_ENTITY,
                    "lineitem request response does not match dict or list",
                )

        # 9. push grades to lineitem
        url_parsed = urlparse(lineitem["id"])
        lineitem = url_parsed._replace(path=url_parsed.path + "/scores").geturl()
        self.log.debug("LTI: start sending grades to LTI course")
        synced_user = 0
        for grade in grades:
            try:
                response = await httpclient.fetch(
                    HTTPRequest(
                        url=lineitem,
                        method="POST",
                        body=json.dumps(grade),
                        headers={
                            "Authorization": "Bearer " + self.cache_token["token"],
                            "Content-Type": "application/vnd.ims.lis.v1.score+json",
                        },
                    )
                )
                synced_user += 1
            except HTTPClientError as e:
                self.log.error(e.response)
        self.log.info("LTI Grade Sync finished successfully")
        return {"syncable_users": syncable_user_count, "synced_user": synced_user}

    def build_grade_publish_body(self, uid: str, score: float, max_score: float):
        return {
            "timestamp": str(
                datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()
            ),
            "scoreGiven": score,
            "comment": "Automatically synced",
            "scoreMaximum": max_score,
            "activityProgress": "Submitted",
            "gradingProgress": "FullyGraded",
            "userId": uid,
        }

    async def request_bearer_token(self):
        # get config variables
        if self.client_id is None:
            raise HTTPError(
                HTTPStatus.NOT_FOUND,
                reason="Unable to request bearer token: client_id is not set in grader config",
            )
        if self.token_url is None:
            raise HTTPError(
                HTTPStatus.NOT_FOUND,
                reason="Unable to request bearer token: token_url is not set in grader config",
            )

        private_key = self.token_private_key
        if private_key is None:
            raise HTTPError(
                HTTPStatus.NOT_FOUND,
                reason="Unable to request bearer token: token_private_key is not set in grader config",
            )
        if callable(private_key):
            private_key = private_key()
        headers = {"typ": "JWT", "alg": "RS256"}
        payload = {
            "iss": "grader-service",
            "sub": self.client_id,
            "aud": ["http://127.0.0.1/mod/lti/token.php"],
            "iat": str(int(time.time())),
            "exp": str(int(time.time()) + 60),
            "jti": str(int(time.time())) + "123",
        }
        try:
            encoded = jwt.encode(payload, private_key, algorithm="RS256", headers=headers)
        except Exception as e:
            raise HTTPError(
                HTTPStatus.UNPROCESSABLE_ENTITY, reason=f"Unable to encode payload: {str(e)}"
            )
        scopes = [
            "https://purl.imsglobal.org/spec/lti-ags/scope/score",
            "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem",
            "https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly",
        ]
        scopes = url_escape(" ".join(scopes))
        data = (
            f"grant_type=client_credentials&client_assertion_type=urn%3Aietf%3Aparams%3Aoauth%3Aclient-assertion"
            f"-type%3Ajwt-bearer&client_assertion={encoded}&scope={scopes}"
        )
        httpclient = AsyncHTTPClient()
        try:
            response = await httpclient.fetch(
                HTTPRequest(
                    url=self.token_url,
                    method="POST",
                    body=data,
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Content-Length": len(data),
                    },
                )
            )
        except HTTPClientError as e:
            self.log.error(e.response)
            raise HTTPError(e.code, reason="Unable to request token:" + e.response.reason)
        return json_decode(response.body)["access_token"]
