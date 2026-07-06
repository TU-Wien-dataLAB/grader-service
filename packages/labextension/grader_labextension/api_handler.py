# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
import tornado

from grader_labextension.handlers.base_handler import ExtensionBaseHandler
from grader_labextension.registry import register_handler


@register_handler(path=r"\/health\/?")
class HealthHandler(ExtensionBaseHandler):
    @tornado.web.authenticated
    def get(self):
        response = {"health": "OK"}
        self.write(response)
