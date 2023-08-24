# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import json
import logging

from jupyter_server.base.handlers import APIHandler, log
from jupyter_server.serverapp import ServerWebApplication
from jupyter_server.utils import url_path_join
import tornado

from grader_service.registry import HandlerPathRegistry, register_handler


@register_handler(path=r"\/health\/?")
class HealthHandler(APIHandler):

    @tornado.web.authenticated
    def get(self):
        response = "Grader Labextension: Health OK"
        self.write(response)



def setup_handlers(web_app: ServerWebApplication):
    host_pattern = ".*$"
    log = logging.getLogger()
    base_url = web_app.settings["base_url"]
    log.info("########################################################################")
    log.info(f'{web_app.settings["server_root_dir"]=}')
    log.info("base_url: " + base_url)
    handlers = HandlerPathRegistry.handler_list(base_url=base_url + "grader_labextension")
    log.info([str(h[0]) for h in handlers])
    web_app.add_handlers(host_pattern, handlers)

