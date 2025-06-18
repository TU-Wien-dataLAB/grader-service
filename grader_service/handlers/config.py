from grader_service.handlers.base_handler import GraderBaseHandler, authorize
from grader_service.orm.takepart import Scope
from grader_service.registry import VersionSpecifier, register_handler


@register_handler(path=r"\/api\/config\/?", version_specifier=VersionSpecifier.ALL)
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
        self.write({})
