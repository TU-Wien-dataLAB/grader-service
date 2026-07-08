# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""LTI-related HTTP handlers (JWKS endpoint)."""

import json

from tornado.web import RequestHandler

from grader_service.registry import VersionSpecifier, register_handler


@register_handler(path=r"\/api\/lti\/jwks\/?", version_specifier=VersionSpecifier.ALL)
class LTIJWKSHandler(RequestHandler):
    """Public endpoint serving a JWKS (JSON Web Key Set) containing the
    RSA public keys used by the grader service to sign LTI token requests.

    One key per configured LTI platform is included, each identified by a
    ``kid`` derived from the platform name.

    No authentication is required.
    """

    async def get(self):
        lti_plugin = self.application.plugin_manager.get("lti")
        jwks = lti_plugin.get_jwks() if lti_plugin else {"keys": []}
        self.set_header("Content-Type", "application/json")
        self.set_header("Cache-Control", "public, max-age=3600")
        self.write(json.dumps(jwks))
