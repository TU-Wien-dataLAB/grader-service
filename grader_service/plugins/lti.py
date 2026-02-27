# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import datetime
import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from http import HTTPStatus
from typing import List, Optional
from urllib.parse import urlparse

import jwt
from cryptography.hazmat.primitives import serialization
from jwt.algorithms import RSAAlgorithm
from tornado.escape import json_decode, url_escape
from tornado.httpclient import AsyncHTTPClient, HTTPClientError, HTTPRequest
from tornado.web import HTTPError
from traitlets import Bool, Callable, Union
from traitlets import Dict as TDict
from traitlets import List as TList

from grader_service.errors import APIError
from grader_service.plugins.base import GraderPlugin, register_plugin

# ---------------------------------------------------------------------------
# Default hook implementations
# ---------------------------------------------------------------------------


def default_lti_username_match(member, submission, platform, log) -> bool:
    """Default username match: no match. Must be overridden in config.

    Args:
        member: LTI member dict from NRPS response.
        submission: Grader submission dict.
        platform: LTIPlatformConfig for the current LTI system.
        log: Logger instance.

    Returns:
        True if the member matches the submission's user.
    """
    return False


def default_enable_lti(lecture, assignment, submissions):
    return False


def default_enable_sync_on_feedback(lecture, assignment, submissions):
    return False


def default_select_systems(lecture, assignment, submissions, platforms):
    """Default: sync to all configured platforms."""
    return [p.name for p in platforms]


def default_resolve_lti_urls(platform, lecture, assignment, submissions):
    """Default URL resolver. Must be overridden in config.

    Args:
        platform: LTIPlatformConfig for the target LTI system.
        lecture: Serialized lecture dict.
        assignment: Serialized assignment dict.
        submissions: List of serialized submission dicts.

    Returns:
        Dict with keys ``lineitems_url`` and ``membership_url``.
    """
    raise NotImplementedError(
        f"resolve_lti_urls must be configured to return membership and lineitem URLs "
        f"for platform '{platform.name}'"
    )


# ---------------------------------------------------------------------------
# LTI Platform configuration dataclass
# ---------------------------------------------------------------------------


@dataclass
class LTIPlatformConfig:
    """Configuration for a single LTI platform / system."""

    name: str
    url_pattern: str
    client_id: str
    token_url: str
    platform_url: str = ""
    private_key_path: str = ""
    deployment_id: str = ""

    # Per-platform bearer-token cache (not serialised)
    _cached_token: Optional[str] = field(default=None, repr=False, compare=False)
    _token_ttl: Optional[datetime.datetime] = field(default=None, repr=False, compare=False)

    # ---- helpers ----------------------------------------------------------

    @property
    def kid(self) -> str:
        """Key ID derived from the platform name: ``sha256(name)[:16]``."""
        return hashlib.sha256(self.name.encode()).hexdigest()[:16]

    def get_private_key(self) -> str:
        """Read the PEM-encoded private key from *private_key_path*."""
        if not self.private_key_path:
            raise ValueError(f"No private_key_path configured for platform '{self.name}'")
        if not os.path.isfile(self.private_key_path):
            raise FileNotFoundError(
                f"Private key file not found for platform '{self.name}': {self.private_key_path}"
            )
        with open(self.private_key_path, "r") as fh:
            return fh.read()

    def get_public_key(self):
        """Derive the RSA public key from the private key."""
        private_key_pem = self.get_private_key()
        private_key = serialization.load_pem_private_key(private_key_pem.encode(), password=None)
        return private_key.public_key()

    def is_token_valid(self) -> bool:
        """Return *True* if the cached bearer token is still usable."""
        if self._cached_token is None or self._token_ttl is None:
            return False
        return self._token_ttl > datetime.datetime.now() - datetime.timedelta(minutes=50)

    def to_dict(self) -> dict:
        """Serialise the public configuration (no secrets)."""
        return {
            "name": self.name,
            "url_pattern": self.url_pattern,
            "client_id": self.client_id,
            "token_url": self.token_url,
            "platform_url": self.platform_url,
            "deployment_id": self.deployment_id,
        }


# ---------------------------------------------------------------------------
# Main LTI Grade-Sync Plugin
# ---------------------------------------------------------------------------


@register_plugin
class LTISyncGrades(GraderPlugin):
    """Multi-platform LTI 1.3 Advantage grade synchronisation plugin.

    Configure one or more LTI systems via the ``systems`` trait.  Each system
    is described by a dict whose keys correspond to :class:`LTIPlatformConfig`
    fields.

    Configurable hooks control which platforms are selected for a given sync
    operation and how grader users are matched to LTI members.

    Access in handlers::

        lti_plugin = self.application.plugin_manager.get("lti")

    Access in celery tasks::

        lti_plugin = self.celery.plugin_manager.get("lti")
    """

    name = "lti"

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
        Determines if submissions should be automatically synchronised on feedback
        generation.  Only synchronises scores when .enabled is True.
        Is either a bool value or
        a function with the params (lecture, assignment, submissions) returning a bool.
        """,
    )

    systems = TList(
        TDict(),
        config=True,
        help="""
        List of LTI platform configurations.  Each entry is a dict with the
        following keys (see :class:`LTIPlatformConfig`):

        - ``name``              - unique identifier for this platform (required)
        - ``url_pattern``       - base URL pattern for matching (required)
        - ``client_id``         - OAuth2 client ID (required)
        - ``token_url``         - OAuth2 token endpoint (required)
        - ``private_key_path``  - path to PEM-encoded RSA private key for JWT signing (required)
        - ``platform_url``      - platform base URL
        - ``deployment_id``     - LTI deployment ID

        Example::

            c.LTISyncGrades.systems = [
                {
                    "name": "MyMoodle",
                    "url_pattern": "https://moodle.university.edu",
                    "client_id": "my-client-id",
                    "token_url": "https://moodle.university.edu/mod/lti/token.php",
                    "platform_url": "https://moodle.university.edu",
                    "private_key_path": "/secrets/lti/private_key.pem",
                    "deployment_id": "1",
                },
            ]
        """,
    )

    resolve_lti_urls = Callable(
        default_value=default_resolve_lti_urls,
        config=True,
        allow_none=True,
        help="""
        Function to resolve LTI membership and lineitem URLs for a platform.

        Signature::

            def resolve(platform: LTIPlatformConfig, lecture, assignment, submissions) -> dict:
                return {"lineitems_url": "...", "membership_url": "..."}
        """,
    )

    username_match = Callable(
        default_value=default_lti_username_match,
        config=True,
        allow_none=True,
        help="""
        Function to match an LTI member to a grader submission for a specific
        platform.

        Signature::

            def match(member, submission, platform: LTIPlatformConfig, log) -> bool
        """,
    )

    select_systems_for_sync = Callable(
        default_value=default_select_systems,
        config=True,
        allow_none=True,
        help="""
        Function to select which LTI platforms to sync grades to for a given
        lecture / assignment / set of submissions.

        Signature::

            def select(lecture, assignment, submissions,
                       platforms: list[LTIPlatformConfig]) -> list[str]

        Returns a list of platform *names* to sync to.
        """,
    )

    # ---- internal state ---------------------------------------------------

    _platforms: List[LTIPlatformConfig] = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._platforms = []

    # ---- platform access --------------------------------------------------

    def _parse_systems(self):
        """Parse the ``systems`` trait into :class:`LTIPlatformConfig` objects."""
        self._platforms = []
        for system_dict in self.systems:
            try:
                platform = LTIPlatformConfig(
                    name=system_dict["name"],
                    url_pattern=system_dict.get("url_pattern", ""),
                    client_id=system_dict["client_id"],
                    token_url=system_dict["token_url"],
                    platform_url=system_dict.get("platform_url", ""),
                    private_key_path=system_dict.get("private_key_path", ""),
                    deployment_id=system_dict.get("deployment_id", ""),
                )
                self._platforms.append(platform)
            except KeyError as exc:
                self.log.error(f"LTI: Missing required key {exc} in system config: {system_dict}")
                raise ValueError(f"Missing required key {exc} in LTI system configuration") from exc

    @property
    def platforms(self) -> List[LTIPlatformConfig]:
        """Lazily parsed list of configured LTI platforms."""
        if not self._platforms and self.systems:
            self._parse_systems()
        return self._platforms

    def get_platform(self, name: str) -> Optional[LTIPlatformConfig]:
        """Look up a platform by *name*; returns ``None`` if not found."""
        for platform in self.platforms:
            if platform.name == name:
                return platform
        return None

    # ---- enable checks ----------------------------------------------------

    def check_if_lti_enabled(self, lecture, assignment, submissions, feedback_sync):
        if callable(self.enabled):
            enable_lti = self.enabled(lecture, assignment, submissions)
        else:
            enable_lti = self.enabled

        if enable_lti:
            if feedback_sync:
                if callable(self.sync_on_feedback):
                    return self.sync_on_feedback(lecture, assignment, submissions)
                return bool(self.sync_on_feedback)
            return True
        return False

    # ---- main entry point -------------------------------------------------

    async def start(self, lecture, assignment, submissions):
        """Run grade sync across all applicable LTI platforms.

        Returns a dict ``{"synced_platforms": [...]}``.
        """
        self.log.info("LTI: start grade sync")
        if len(submissions) == 0:
            raise HTTPError(HTTPStatus.BAD_REQUEST, reason="No submissions to sync")

        if not self.platforms:
            raise HTTPError(HTTPStatus.BAD_REQUEST, reason="No LTI systems configured")

        # Determine which platforms to sync to
        selected_names = self.select_systems_for_sync(
            lecture, assignment, submissions, self.platforms
        )
        selected_platforms = [p for p in self.platforms if p.name in selected_names]

        if not selected_platforms:
            self.log.warning("LTI: No platforms selected for sync")
            return {"synced_platforms": []}

        results = []
        for platform in selected_platforms:
            try:
                result = await self._sync_platform(platform, lecture, assignment, submissions)
                results.append({"platform": platform.name, **result})
            except Exception as exc:
                self.log.error(f"LTI: Failed to sync to platform '{platform.name}': {exc}")
                results.append(
                    {
                        "platform": platform.name,
                        "error": str(exc),
                        "syncable_users": 0,
                        "synced_user": 0,
                    }
                )

        return {"synced_platforms": results}

    # ---- per-platform sync ------------------------------------------------

    async def _sync_platform(self, platform: LTIPlatformConfig, lecture, assignment, submissions):
        """Sync grades to a single LTI platform."""
        self.log.info(f"LTI [{platform.name}]: syncing grades")

        # 1. bearer token
        self.log.debug(f"LTI [{platform.name}]: request bearer token")
        if platform.is_token_valid():
            token = platform._cached_token
        else:
            token = await self.request_bearer_token(platform)
            platform._cached_token = token
            platform._token_ttl = datetime.datetime.now()

        # 2. resolve lti urls
        self.log.debug(f"LTI [{platform.name}]: resolve lti urls")
        try:
            lti_urls = self.resolve_lti_urls(platform, lecture, assignment, submissions)
            self.log.debug(f"LTI [{platform.name}] URLs: {lti_urls}")
            lineitems_url = lti_urls["lineitems_url"]
            membership_url = lti_urls["membership_url"]
        except Exception as exc:
            self.log.error(f"LTI [{platform.name}]: failed to resolve URLs: {exc}")
            raise exc

        httpclient = AsyncHTTPClient()

        # 3. get all members
        self.log.debug(f"LTI [{platform.name}]: fetching course members")
        try:
            response = await httpclient.fetch(
                HTTPRequest(
                    url=membership_url,
                    method="GET",
                    headers={
                        "Authorization": "Bearer " + token,
                        "Accept": "application/vnd.ims.lti-nrps.v2.membershipcontainer+json",
                    },
                )
            )
        except HTTPClientError as exc:
            self.log.error(exc.response)
            raise HTTPError(
                exc.code,
                reason=f"Unable to get users from '{platform.name}': {exc.response.reason}",
            )
        members = json_decode(response.body)["members"]

        # 4. match submissions to members
        self.log.debug(f"LTI [{platform.name}]: matching usernames")
        grades = []
        syncable_user_count = 0
        for submission in submissions:
            for member in members:
                if self.username_match(member, submission, platform, self.log):
                    syncable_user_count += 1
                    grades.append(
                        self.build_grade_publish_body(
                            member["user_id"], submission["score"], float(assignment["points"])
                        )
                    )
        self.log.info(f"LTI [{platform.name}]: matched {syncable_user_count} users")

        # 5. get lineitems
        self.log.debug(f"LTI [{platform.name}]: fetching lineitems")
        try:
            response = await httpclient.fetch(
                HTTPRequest(
                    url=lineitems_url,
                    method="GET",
                    headers={
                        "Authorization": "Bearer " + token,
                        "Accept": "application/vnd.ims.lis.v2.lineitemcontainer+json",
                    },
                )
            )
        except HTTPClientError as exc:
            self.log.error(exc.response)
            raise HTTPError(
                exc.code,
                reason=f"Unable to get lineitems from '{platform.name}': {exc.response.reason}",
            )
        lineitems = json_decode(response.body)
        self.log.debug(f"LTI [{platform.name}] lineitems: {lineitems}")

        # 6. find or create lineitem
        lineitem = None
        for item in lineitems:
            if item["label"] == assignment["name"]:
                self.log.debug(f"LTI [{platform.name}] found lineitem: {item}")
                lineitem = item
                break

        if lineitem is None:
            lineitem = await self._create_lineitem(
                httpclient, lineitems_url, token, platform, assignment
            )

        # 7. push grades
        url_parsed = urlparse(lineitem["id"])
        scores_url = url_parsed._replace(path=url_parsed.path + "/scores").geturl()
        self.log.debug(f"LTI [{platform.name}]: sending grades")
        synced_user = 0
        for grade in grades:
            try:
                await httpclient.fetch(
                    HTTPRequest(
                        url=scores_url,
                        method="POST",
                        body=json.dumps(grade),
                        headers={
                            "Authorization": "Bearer " + token,
                            "Content-Type": "application/vnd.ims.lis.v1.score+json",
                        },
                    )
                )
                synced_user += 1
            except HTTPClientError as exc:
                self.log.error(f"LTI [{platform.name}]: failed to sync grade: {exc.response}")
        self.log.info(f"LTI [{platform.name}]: Grade Sync finished")
        return {"syncable_users": syncable_user_count, "synced_user": synced_user}

    # ---- lineitem helpers -------------------------------------------------

    async def _create_lineitem(self, httpclient, lineitems_url, token, platform, assignment):
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
                        "Authorization": "Bearer " + token,
                        "Content-Type": "application/vnd.ims.lis.v2.lineitem+json",
                    },
                )
            )
        except HTTPClientError as exc:
            self.log.error(exc.response)
            raise HTTPError(
                exc.code,
                reason=(f"Unable to create lineitem in '{platform.name}': {exc.response.reason}"),
            )
        # LMS implementations vary: response may be a list or a dict
        try:
            lineitem_response = json_decode(response.body)
        except Exception as exc:
            self.log.error(f"LTI [{platform.name}]: could not decode lineitem response")
            raise exc
        if isinstance(lineitem_response, list):
            return lineitem_response[0]
        if isinstance(lineitem_response, dict):
            return lineitem_response
        self.log.error(f"LTI [{platform.name}]: lineitem response is neither dict nor list")
        raise HTTPError(
            HTTPStatus.UNPROCESSABLE_ENTITY, "lineitem response does not match dict or list"
        )

    # ---- score body builder -----------------------------------------------

    @staticmethod
    def build_grade_publish_body(uid: str, score: float, max_score: float):
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

    # ---- bearer token request ---------------------------------------------

    async def request_bearer_token(self, platform: LTIPlatformConfig):
        """Request a bearer token for a specific LTI platform using
        OAuth 2.0 client_credentials with a JWT assertion.

        The JWT includes a ``kid`` header derived from the platform name
        (``sha256(name)[:16]``).
        """
        if not platform.client_id:
            raise HTTPError(
                HTTPStatus.NOT_FOUND, reason=f"client_id not set for platform '{platform.name}'"
            )
        if not platform.token_url:
            raise HTTPError(
                HTTPStatus.NOT_FOUND, reason=f"token_url not set for platform '{platform.name}'"
            )

        try:
            private_key = platform.get_private_key()
        except (ValueError, FileNotFoundError) as exc:
            raise APIError(
                HTTPStatus.NOT_FOUND,
                message=f"Unable to load private key for platform '{platform.name}': {exc}",
            )

        kid = platform.kid
        headers = {"typ": "JWT", "alg": "RS256", "kid": kid}
        payload = {
            "iss": "grader-service",
            "sub": platform.client_id,
            "aud": [platform.token_url],
            "iat": str(int(time.time())),
            "exp": str(int(time.time()) + 60),
            "jti": str(int(time.time())) + "123",
        }
        try:
            encoded = jwt.encode(payload, private_key, algorithm="RS256", headers=headers)
        except Exception as exc:
            raise APIError(
                HTTPStatus.UNPROCESSABLE_ENTITY, message=f"Unable to encode payload: {exc}"
            )
        scopes = [
            "https://purl.imsglobal.org/spec/lti-ags/scope/score",
            "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem",
            "https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly",
        ]
        scopes = url_escape(" ".join(scopes))
        data = (
            f"grant_type=client_credentials"
            f"&client_assertion_type=urn%3Aietf%3Aparams%3Aoauth%3Aclient-assertion"
            f"-type%3Ajwt-bearer&client_assertion={encoded}&scope={scopes}"
        )
        httpclient = AsyncHTTPClient()
        try:
            response = await httpclient.fetch(
                HTTPRequest(
                    url=platform.token_url,
                    method="POST",
                    body=data,
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Content-Length": len(data),
                    },
                )
            )
        except HTTPClientError as exc:
            self.log.error(exc.response)
            raise HTTPError(
                exc.code,
                reason=(f"Unable to request token from '{platform.name}': {exc.response.reason}"),
            )
        return json_decode(response.body)["access_token"]

    # ---- JWKS generation --------------------------------------------------

    def get_jwks(self) -> dict:
        """Build a JWKS (JSON Web Key Set) containing the public keys of all
        configured platforms.

        Each key's ``kid`` is ``sha256(platform_name)[:16]``.
        """
        keys = []
        for platform in self.platforms:
            try:
                public_key = platform.get_public_key()
                jwk_str = RSAAlgorithm.to_jwk(public_key)
                jwk_dict = json.loads(jwk_str) if isinstance(jwk_str, str) else jwk_str
                jwk_dict["kid"] = platform.kid
                jwk_dict["alg"] = "RS256"
                jwk_dict["use"] = "sig"
                keys.append(jwk_dict)
            except Exception as exc:
                self.log.warning(
                    f"LTI: Could not generate JWK for platform '{platform.name}': {exc}"
                )
        return {"keys": keys}
