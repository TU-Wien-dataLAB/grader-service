"""Authorization handlers"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
import json
from typing import Awaitable, Optional
from unittest import mock
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from oauthlib import oauth2
from tornado import web

from grader_service.handlers.base_handler import BaseHandler
from grader_service.orm.api_token import APIToken
from grader_service.utils import get_browser_protocol, url_path_join


class SelfAPIHandler(BaseHandler):
    """Return the authenticated user's model

    Based on the authentication info. Acts as a 'whoami' for auth tokens.
    """

    async def get(self):
        user = self.current_user
        if user is None:
            raise web.HTTPError(403)
        model = user.model.to_dict()

        # add session_id associated with token
        # added in 2.0
        # token_id added in 5.0
        token = self.get_token()
        if token:
            model["token_id"] = token.api_id
            model["session_id"] = token.session_id
        else:
            model["token_id"] = None
            model["session_id"] = None
        model["roles"] = [f"{r.lecture.code}:{r.role.name}" for r in user.roles]
        self.write(json.dumps(model))


class OAuthHandler:
    def extract_oauth_params(self):
        """extract oauthlib params from a request

        Returns:

        (uri, http_method, body, headers)
        """
        return (self.request.uri, self.request.method, self.request.body, self.request.headers)

    def make_absolute_redirect_uri(self, uri):
        """Make absolute redirect URIs

        internal redirect uris, e.g. `/user/foo/oauth_handler`
        are allowed in jupyterhub, but oauthlib prohibits them.
        Add `$HOST` header to redirect_uri to make them acceptable.

        Currently unused in favor of monkeypatching
        oauthlib.is_absolute_uri to skip the check
        """
        redirect_uri = self.get_argument("redirect_uri")
        if not redirect_uri or not redirect_uri.startswith("/"):
            return uri
        # make absolute local redirects full URLs
        # to satisfy oauthlib's absolute URI requirement
        redirect_uri = get_browser_protocol(self.request) + "://" + self.request.host + redirect_uri
        parsed_url = urlparse(uri)
        query_list = parse_qsl(parsed_url.query, keep_blank_values=True)
        for idx, item in enumerate(query_list):
            if item[0] == "redirect_uri":
                query_list[idx] = ("redirect_uri", redirect_uri)
                break

        return urlunparse(urlparse(uri)._replace(query=urlencode(query_list)))

    def add_credentials(self, credentials=None):
        """Add oauth credentials

        Adds user, session_id, client to oauth credentials
        """
        if credentials is None:
            credentials = {}
        else:
            credentials = credentials.copy()

        session_id = self.get_session_cookie()
        if session_id is None:
            session_id = self.set_session_cookie()

        user = self.current_user

        # Extra credentials we need in the validator
        credentials.update({"user": user, "handler": self, "session_id": session_id})
        return credentials

    def send_oauth_response(self, headers, body, status):
        """Send oauth response from provider return values

        Provider methods return headers, body, and status
        to be set on the response.

        This method applies these values to the Handler
        and sends the response.
        """
        self.set_status(status)
        for key, value in headers.items():
            self.set_header(key, value)
        if body:
            self.write(body)


class OAuthAuthorizeHandler(OAuthHandler, BaseHandler):
    """Implement OAuth authorization endpoint(s)"""

    def prepare(self) -> Optional[Awaitable[None]]:
        return super().prepare()

    def _complete_login(self, uri, headers, scopes, credentials):
        try:
            headers, body, status = self.application.oauth_provider.create_authorization_response(
                uri, "POST", "", headers, scopes, credentials
            )

        except oauth2.FatalClientError:
            # TODO: human error page
            raise
        self.send_oauth_response(headers, body, status)

    def needs_oauth_confirm(self, user, oauth_client, requested_scopes):
        """Return whether the given oauth client needs to prompt for access for the given user

        Checks list for oauth clients that don't need confirmation

        Sources:

        - the user's own servers
        - Clients which already have authorization for the same roles
        - Explicit oauth_no_confirm_list configuration (e.g. admin-operated services)

        .. versionadded: 1.1
        """
        # get the oauth client ids for the user's own server(s)
        own_oauth_client_ids = {spawner.oauth_client_id for spawner in user.spawners.values()}
        if (
            # it's the user's own server
            oauth_client.identifier in own_oauth_client_ids
            # or it's in the global no-confirm list
            or oauth_client.identifier in self.settings.get("oauth_no_confirm_list", set())
        ):
            return False

        # Check existing authorization
        existing_tokens = self.session.query(APIToken).filter_by(
            username=user.name, client_id=oauth_client.identifier
        )
        authorized_scopes = set()
        for token in existing_tokens:
            authorized_scopes.update(token.scopes)

        if authorized_scopes:
            if set(requested_scopes).issubset(authorized_scopes):
                self.log.debug(
                    f"User {user.name} has already authorized {oauth_client.identifier} for scopes {requested_scopes}"
                )
                return False
            else:
                self.log.debug(
                    f"User {user.name} has authorized {oauth_client.identifier}"
                    f" for scopes {authorized_scopes}, confirming additional scopes {requested_scopes}"
                )
        # default: require confirmation
        return True

    def get_login_url(self):
        """
        Support automatically logging in when JupyterHub is used as auth provider
        """
        if self.authenticator.auto_login_oauth2_authorize:
            return self.authenticator.login_url(self.application.base_url)
        return super().get_login_url()

    async def get(self):
        """GET /api/oauth2/authorize

        Render oauth confirmation page:
        "Server at ... would like permission to ...".

        Users accessing their own server or a blessed service
        will skip confirmation.
        """
        uri, http_method, body, headers = self.extract_oauth_params()
        try:
            with mock.patch.object(
                self.oauth_provider.request_validator,
                "_current_user",
                self.current_user,
                create=True,
            ):
                (requested_scopes, credentials) = (
                    self.oauth_provider.validate_authorization_request(
                        uri, http_method, body, headers
                    )
                )
            credentials = self.add_credentials(credentials)
            client = self.oauth_provider.fetch_by_client_id(credentials["client_id"])

            # Render oauth 'Authorize application...' page
            auth_state = await self.current_user.get_auth_state()
            self.write(
                await self.render_template(
                    "auth/oauth.html.j2", auth_state=auth_state, oauth_client=client
                )
            )

        # Errors that should be shown to the user on the provider website
        except oauth2.FatalClientError as e:
            raise web.HTTPError(e.status_code, e.description)

        # Errors embedded in the redirect URI back to the client
        except oauth2.OAuth2Error as e:
            self.log.error("OAuth error: %s", e.description)
            self.redirect(e.in_uri(e.redirect_uri))

    def post(self):
        uri, http_method, body, headers = self.extract_oauth_params()
        # The scopes the user actually authorized, i.e. checkboxes
        # that were selected.
        scopes = self.get_arguments("scopes")
        if scopes == []:
            # avoid triggering default scopes (provider selects default scopes when scopes is falsy)
            # when an explicit empty list is authorized
            scopes = ["identify"]
        # credentials we need in the validator
        credentials = self.add_credentials()

        try:
            headers, body, status = self.application.oauth_provider.create_authorization_response(
                uri, http_method, body, headers, scopes, credentials
            )
        except oauth2.FatalClientError as e:
            raise web.HTTPError(e.status_code, e.description)
        else:
            self.send_oauth_response(headers, body, status)


class OAuthTokenHandler(OAuthHandler, BaseHandler):
    def post(self):
        uri, http_method, body, headers = self.extract_oauth_params()
        credentials = {}

        try:
            headers, body, status = self.application.oauth_provider.create_token_response(
                uri, http_method, body, headers, credentials
            )
        except oauth2.FatalClientError as e:
            raise web.HTTPError(e.status_code, e.description)
        else:
            self.send_oauth_response(headers, body, status)


def get_oauth_default_handlers(base_path: str):
    return [
        (url_path_join(base_path, "/api/user"), SelfAPIHandler),
        (url_path_join(base_path, "/api/oauth2/authorize"), OAuthAuthorizeHandler),
        (url_path_join(base_path, "/api/oauth2/token"), OAuthTokenHandler),
    ]
