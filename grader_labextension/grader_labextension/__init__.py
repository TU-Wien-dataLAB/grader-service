import asyncio

from tornado.httpclient import HTTPClientError

from grader_labextension.registry import HandlerPathRegistry
from grader_labextension.handlers.base_handler import HandlerConfig
from traitlets.config.loader import Config
from grader_labextension.services.request import RequestService


def _jupyter_labextension_paths():
    return [{
        "src": "labextension",
        "dest": "grader-labextension"
    }]


def _jupyter_server_extension_points():
    return [{
        "module": "grader_labextension"
    }]


def _load_jupyter_server_extension(server_app):
    """Register API handlers to receive HTTP requests from frontend extension.

    Parameters
    ----------
    server_app: jupyterlab.labapp.LabApp
        JupyterLab application instance
    """
    setup_handlers(server_app)
    name = "grader_labextension"
    server_app.log.info(f"Registered {name} server extension")


def setup_handlers(server_app):
    web_app = server_app.web_app
    config = server_app.config
    log = server_app.log

    host_pattern = ".*$"
    settings = web_app.settings
    if 'page_config_data' not in settings:
        settings['page_config_data'] = {}

    request_service = RequestService.instance(config=config)
    handler_config = HandlerConfig.instance(config=config)

    # add lecture_base_path
    settings['page_config_data']["lectures_base_path"] = handler_config.lectures_base_path
    async def get_grader_config():
        log.info("Loading config from grader service...")
        try:
            response: dict = await request_service.request(
                "GET",
                f"{handler_config.service_base_url}/config",
                header=dict(
                    Authorization="Token " + HandlerConfig.instance().hub_api_token),
            )
        except HTTPClientError as e:
            log.error("Error: could not get grader config")
            log.error(e.response)
            response = dict()
        for key, value in response.items():
            web_app.settings['page_config_data'][key] = value

    # add grader config
    asyncio.run(get_grader_config())
    log.info(f"Grader page_config_data: {web_app.settings['page_config_data']}")

    base_url = settings["base_url"]
    log.info(f'{web_app.settings["server_root_dir"]=}')
    log.info("base_url: " + base_url)
    handlers = HandlerPathRegistry.handler_list(
        base_url=base_url + "grader_labextension")
    log.info("Subscribed handlers:")
    log.info([str(h[0]) for h in handlers])

    web_app.add_handlers(host_pattern, handlers)



# For backward compatibility with notebook server, useful for Binder/JupyterHub
load_jupyter_server_extension = _load_jupyter_server_extension
