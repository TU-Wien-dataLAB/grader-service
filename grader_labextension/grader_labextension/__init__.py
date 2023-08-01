# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
import asyncio
import json
import logging
import shutil
import sys
from pathlib import Path
from grader_labextension.services.request import RequestService
from grader_labextension.handlers.base_handler import HandlerConfig
from tornado.httpclient import HTTPClientError
from jupyter_server.serverapp import ServerApp, ServerWebApplication
from traitlets.config.loader import Config

from ._version import __version__

HERE = Path(__file__).parent.resolve()

with (HERE / "labextension" / "package.json").open() as fid:
    data = json.load(fid)


def _jupyter_labextension_paths():
    return [{
        "src": "labextension",
        "dest": data["name"]
    }]


# unused import to register handlers
from grader_labextension import handlers
from grader_labextension.registry import HandlerPathRegistry


def validate_system_environment():
    if sys.version_info.major < 3 or sys.version_info.minor < 10:
        raise RuntimeError("This extension needs Python version 3.10 or above to run!")
    if shutil.which("git") is None:
        raise RuntimeError("No git executable found! Git is necessary to run the extension!")


def setup_handlers(web_app: ServerWebApplication, config: Config, log: logging.Logger):
    host_pattern = ".*$"
    base_url = web_app.settings["base_url"]
    settings = web_app.settings
    if 'page_config_data' not in settings:
        settings['page_config_data'] = {}

    request_service = RequestService.instance(config=config)
    handler_config = HandlerConfig.instance(config=config)

    settings['page_config_data']["lectures_base_path"] = handler_config.lectures_base_path
    log.info(web_app.settings)

    async def get_grader_config():
        log.info("Loading config from grader service...")
        try:
            response: dict = await request_service.request(
                "GET",
                f"{handler_config.service_base_url}/config",
                header=dict(Authorization="Token " + HandlerConfig.instance().hub_api_token),
            )
        except HTTPClientError as e:
            log.error(e.response)
            response = dict()
        for key, value in response.items():
            web_app.settings['page_config_data'][key] = value

    asyncio.run(get_grader_config())
    log.info(f"Grader page_config_data: {web_app.settings['page_config_data']}")

    handlers = HandlerPathRegistry.handler_list(base_url=base_url + "grader_labextension")
    web_app.add_handlers(host_pattern, handlers)


def _jupyter_server_extension_points():
    return [{
        "module": "grader_labextension"
    }]


def _load_jupyter_server_extension(server_app: ServerApp):
    """Registers the API handler to receive HTTP requests from the frontend extension.

    Parameters
    ----------
    server_app: jupyterlab.labapp.LabApp
        JupyterLab application instance
    """
    server_app.log.info(f"Config paths: {server_app.config_file_paths}")
    setup_handlers(server_app.web_app, server_app.config, server_app.log)
    server_app.log.info("Registered grading extension at URL path /grader_labextension")
