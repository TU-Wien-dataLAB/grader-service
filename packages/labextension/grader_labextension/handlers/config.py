from tornado.web import HTTPError, authenticated

from grader_labextension.handlers.base_handler import ExtensionBaseHandler
from grader_labextension.registry import register_handler
from grader_labextension.services.request import RequestServiceError


@register_handler(path=r"api\/config\/?")
class ConfigHandler(ExtensionBaseHandler):
    @authenticated
    async def get(self):
        try:
            # see setup_handlers() and get_grader_config() in __init__.py of grader_labextension
            data = self.settings["page_config_data"]
            cell_timeout_keys = ["default_cell_timeout", "min_cell_timeout", "max_cell_timeout"]
            cell_timeout_data = {k: data[k] for k in cell_timeout_keys}
            self.log.info("Retrived config values for cell timeout: %s", cell_timeout_data)
            self.write(data)
        except RequestServiceError as e:
            self.log.error(e)
            raise HTTPError(e.code, reason=str(e))
        except KeyError as e:
            self.log.error(e)
            raise HTTPError(500, reason=str(e))
