import os
from typing import Any, Optional

from tornado import httputil
from tornado.web import StaticFileHandler

from grader_service.registry import register_handler
from grader_service.server import GraderServer


class CacheControlStaticFilesHandler(StaticFileHandler):
    """StaticFileHandler subclass that sets Cache-Control: no-cache without `?v=`

    rather than relying on default browser cache behavior.
    """

    def compute_etag(self):
        return None

    def set_extra_headers(self, path):
        if "v" not in self.request.arguments or self.settings.get("no_cache_static", False):
            self.add_header("Cache-Control", "no-cache")


@register_handler(r"\/logo")
class LogoHandler(StaticFileHandler):
    """A singular handler for serving the logo."""

    def __init__(
        self, application: "GraderServer", request: httputil.HTTPServerRequest, **kwargs: Any
    ) -> None:
        super().__init__(application, request, **kwargs)
        self.application: GraderServer = self.application

    def initialize(self, default_filename: Optional[str] = None) -> None:
        path = self.application.logo_file
        super().initialize(path, default_filename)

    def get(self):
        return super().get("")

    @classmethod
    def get_absolute_path(cls, root, path):
        """We only serve one file, ignore relative path"""
        return os.path.abspath(root)
