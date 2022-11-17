import json

from tornado import web
from tornado.httpclient import HTTPClientError

from grader_labextension.handlers.base_handler import ExtensionBaseHandler, cache
from grader_labextension.registry import register_handler


@register_handler(path=r"\/config\/?")
class ConfigHandler(ExtensionBaseHandler):
    """
    Tornado Handler class for http requests to /config.
    """

    @web.authenticated
    @cache(max_age=50)
    async def get(self):
        """ Sends a GET-request to the grader service and returns the relevant config for the lab extension.
        """
        try:
            response = await self.request_service.request(
                "GET",
                f"{self.service_base_url}/config",
                header=self.grader_authentication_header,
                response_callback=self.set_service_headers
            )
        except HTTPClientError as e:
            self.log.error(e.response)
            raise web.HTTPError(e.code, reason=e.response.reason)
        self.write(json.dumps(response))
