# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import json
import logging
import shutil
import sys
from pathlib import Path
from grader_labextension.services.request import RequestService
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
    if sys.version_info.major < 3 or sys.version_info.minor < 7:
        raise RuntimeError("This extension needs Python version 3.7 or above to run!")
    if shutil.which("git") is None:
        raise RuntimeError("No git executable found! Git is necessary to run the extension!")


def setup_handlers(web_app: ServerWebApplication, config: Config):
    host_pattern = ".*$"
    # RequestService.config = web_app.config
    base_url = web_app.settings["base_url"]
    log = logging.getLogger()
    log.info("#######################################################################")
    log.info(f'{web_app.settings["server_root_dir"]=}')
    log.info("base_url: " + base_url)
    handlers = HandlerPathRegistry.handler_list(base_url=base_url + "grader_labextension")
    log.info([str(h[0]) for h in handlers])
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

    setup_handlers(server_app.web_app, server_app.config)
    server_app.log.info("Registered grading extension at URL path /grader_labextension")
