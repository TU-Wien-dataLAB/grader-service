try:
    from ._version import __version__
except ImportError:
    # Fallback when using the package in dev mode without installing
    # in editable mode with pip. It is highly recommended to install
    # the package from a stable release or in editable mode: https://pip.pypa.io/en/stable/topics/local-project-installs/#editable-installs
    import warnings

    warnings.warn("Importing 'grader_labextension' outside a proper installation.")
    __version__ = "dev"

import asyncio

from grader_labextension.handlers.base_handler import HandlerConfig
from grader_labextension.registry import HandlerPathRegistry
from grader_labextension.services.request import RequestServiceError


def _jupyter_labextension_paths():
    return [{"src": "labextension", "dest": "grader-labextension"}]


def _jupyter_server_extension_points():
    return [{"module": "grader_labextension"}]


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
    # config = server_app.config
    log = server_app.log

    host_pattern = ".*$"
    settings = web_app.settings
    if "page_config_data" not in settings:
        settings["page_config_data"] = {}

    handler_config = HandlerConfig.instance()

    # add lecture_base_path
    settings["page_config_data"]["lectures_base_path"] = handler_config.lectures_base_path

    async def get_grader_config():
        log.info("Loading config from grader service...")
        # Retry logic for DNS resolution issues
        for attempt in range(3):
            try:
                # Create a fresh RequestService to get a new HTTP client
                from grader_labextension.services.request import RequestService

                RequestService.clear_instance()
                request_service = RequestService.instance()

                response: dict = await request_service.request(
                    "GET",
                    f"{handler_config.service_base_url}api/config",
                    header=dict(Authorization="Token " + handler_config.grader_api_token),
                )
                break  # Success
            except RequestServiceError as e:
                log.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    await asyncio.sleep(1)  # Wait before retry
                else:
                    log.error("All attempts failed, using empty config")
                    response = dict()
            except Exception as e:
                log.error(f"Unexpected error: {e}")
                if attempt < 2:
                    await asyncio.sleep(1)
                else:
                    response = dict()
        for key, value in response.items():
            web_app.settings["page_config_data"][key] = value

    # add grader config
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # In test environment or when loop is already running
        # Schedule the task to run in the background (fire-and-forget)
        # Handlers will work with default values if config isn't loaded yet
        async def load_config_with_error_handling():
            try:
                await get_grader_config()
            except Exception as e:
                log.error(f"Failed to load grader config: {e}")

        asyncio.ensure_future(load_config_with_error_handling())
        log.info("Grader config loading scheduled (async)")
    else:
        loop.run_until_complete(get_grader_config())
        log.info(f"Grader page_config_data: {web_app.settings['page_config_data']}")

    base_url = settings["base_url"]
    log.info(f'{web_app.settings["server_root_dir"]=}')
    log.info("base_url: " + base_url)
    handlers = HandlerPathRegistry.handler_list(base_url=base_url + "grader_labextension/")
    log.info("Subscribed handlers:")
    log.info([str(h[0]) for h in handlers])

    web_app.add_handlers(host_pattern, handlers)


# For backward compatibility with notebook server, useful for Binder/JupyterHub
load_jupyter_server_extension = _load_jupyter_server_extension
