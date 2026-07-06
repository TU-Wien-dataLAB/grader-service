# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import json

from tornado.web import HTTPError, authenticated

from grader_labextension.handlers.base_handler import ExtensionBaseHandler
from grader_labextension.registry import register_handler
from grader_labextension.services.request import RequestServiceError


@register_handler(path=r"api\/permissions\/?")
class PermissionBaseHandler(ExtensionBaseHandler):
    """
    Tornado Handler class for http requests to /permissions.
    """

    @authenticated
    async def get(self):
        """Sends a GET-request to the grader service and returns the permissions of a user"""
        try:
            response = await self.request_service.request_with_retries(
                "GET",
                f"{self.service_base_url}api/permissions",
                header=self.grader_authentication_header,
                response_callback=self.set_service_headers,
            )
        except RequestServiceError as e:
            self.log.error(e)
            raise HTTPError(e.code, reason=e.message)
        except Exception as e:
            self.log.error(f"Unexpected Error: {e}")
            raise HTTPError(e)
        self.write(json.dumps(response))
