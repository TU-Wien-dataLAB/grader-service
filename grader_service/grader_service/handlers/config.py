from grader_service.handlers.base_handler import GraderBaseHandler, RequestHandlerConfig, authorize
from grader_service.orm.takepart import Scope
from grader_service.registry import register_handler, VersionSpecifier


@register_handler(
    path=r"\/config\/?",
    version_specifier=VersionSpecifier.ALL,
)
class ConfigHandler(GraderBaseHandler):
    """
    Handler class for requests to /config
    """

    @authorize([Scope.student, Scope.tutor, Scope.instructor])
    async def get(self):
        """
        Gathers useful config for the grader labextension and returns it.
        :return: config in dict
        """
        handler_config = RequestHandlerConfig.instance()
        self.write({"enable_lti_features": handler_config.enable_lti_features})
