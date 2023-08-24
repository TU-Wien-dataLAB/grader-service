# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
import tornado
from grader_labextension.handlers.base_handler import ExtensionBaseHandler
from grader_labextension.registry import HandlerPathRegistry, register_handler


@register_handler(path=r"\/health\/?")
class HealthHandler(ExtensionBaseHandler):

    @tornado.web.authenticated
    def get(self):
        response = "Grader Labextension: Health OK"
        self.write(response)


def setup_handlers(server_app):
    web_app = server_app.web_app
    host_pattern = ".*$"
    base_url = web_app.settings["base_url"]
    server_app.log.info("########################################################################")
    server_app.log.info(f'{web_app.settings["server_root_dir"]=}')
    server_app.log.info("base_url: " + base_url)
    handlers = HandlerPathRegistry.handler_list(
        base_url=base_url + "grader_labextension")
    server_app.log.info([str(h[0]) for h in handlers])
    web_app.add_handlers(host_pattern, handlers)
