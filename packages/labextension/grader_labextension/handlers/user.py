from grader_service.handlers.base_handler import authenticated

from grader_labextension.handlers.base_handler import ExtensionBaseHandler
from grader_labextension.registry import register_handler


@register_handler(r"api\/user\/?")
class UserHandler(ExtensionBaseHandler):
    @authenticated
    def get(self):
        self.write(self.user_name)
