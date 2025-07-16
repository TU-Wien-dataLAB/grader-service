"""HTTP Handlers for the hub server"""

from typing import Awaitable, Optional

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
from jinja2 import Template
from tornado import web
from tornado.escape import url_escape
from tornado.httputil import url_concat

from grader_service.handlers.base_handler import BaseHandler


class LogoutHandler(BaseHandler):
    """Log a user out by clearing their login cookie."""

    def _backend_logout_cleanup(self, name):
        """Default backend logout actions"""
        self.log.info("User logged out: %s", name)
        self.clear_login_cookies()

    async def default_handle_logout(self):
        """The default logout action

        Optionally cleans up servers, clears cookies, increments logout counter
        Cleaning up servers can be prevented by setting shutdown_on_logout to
        False.
        """
        user = self.current_user
        if user:
            self._backend_logout_cleanup(user.name)

    async def handle_logout(self):
        """Custom user action during logout

        By default a no-op, this function should be overridden in subclasses
        to have JupyterHub take a custom action on logout.
        """
        return

    async def render_logout_page(self):
        """Render the logout page, if any

        Override this function to set a custom logout page.
        """
        if self.authenticator.auto_login:
            html = await self.render_template("auth/logout.html.j2")
            self.finish(html)
        else:
            self.redirect(self.settings["login_url"], permanent=False)

    async def get(self):
        """Log the user out, call the custom action, forward the user
        to the logout page
        """
        await self.default_handle_logout()
        await self.handle_logout()
        # clear grader user before rendering logout page
        # ensures the login button is shown instead of logout
        self._grader_user = None
        await self.render_logout_page()


class LoginHandler(BaseHandler):
    """Render the login page."""

    def _render(self, login_error=None, username=None):
        context = {
            "next": url_escape(self.get_argument("next", default="")),
            "username": username,
            "login_error": login_error,
            "login_url": self.settings["login_url"],
            "authenticator_login_url": url_concat(
                self.authenticator.login_url(self.application.base_url),
                {"next": self.get_argument("next", "")},
            ),
            "authenticator": self.authenticator,
            "xsrf": self.xsrf_token.decode("ascii"),
        }
        custom_html = Template(
            self.authenticator.get_custom_html(self.application.base_url)
        ).render(**context)
        return self.render_template("auth/login.html.j2", **context, custom_html=custom_html)

    async def prepare(self) -> Optional[Awaitable[None]]:
        await super().prepare()
        return

    async def get(self):
        user = self.current_user
        if user:
            # set new login cookie
            # because single-user cookie may have been cleared or incorrect
            self.set_login_cookie(user)
            self.redirect(self.get_next_url(user), permanent=False)
        else:
            if self.authenticator.auto_login:
                auto_login_url = self.authenticator.login_url(self.application.base_url)
                if auto_login_url == self.settings["login_url"]:
                    # auto_login without a custom login handler
                    # means that auth info is already in the request
                    # (e.g. REMOTE_USER header)
                    user = await self.login_user()
                    if user is None:
                        # auto_login failed, just 403
                        raise web.HTTPError(403)
                    else:
                        self.redirect(self.get_next_url(user))
                else:
                    if self.get_argument("next", default=False):
                        auto_login_url = url_concat(auto_login_url, {"next": self.get_next_url()})
                    self.redirect(auto_login_url)
                return
            username = self.get_argument("username", default="")
            self.finish(await self._render(username=username))

    async def post(self):
        # parse the arguments dict
        data = {}
        for arg in self.request.body_arguments:
            if arg == "_xsrf":
                # don't include xsrf token in auth input
                continue
            # strip username, but not other fields like passwords,
            # which should be allowed to start or end with space
            data[arg] = self.get_argument(arg, strip=arg == "username")

        user = await self.login_user(data)

        if user:
            # register current user for subsequent requests to user (e.g. logging the request)
            self._grader_user = user
            self.redirect(self.get_next_url(user))
        else:
            html = await self._render(
                login_error="Invalid username or password", username=data["username"]
            )
            self.set_status(404)
            await self.finish(html)
