from grader_service.orm.takepart import Role, Scope
from grader_service.registry import VersionSpecifier, register_handler

from grader_service.handlers.base_handler import GraderBaseHandler, authorize


@register_handler(path=r"\/permissions\/?", version_specifier=VersionSpecifier.ALL)
class PermissionHandler(GraderBaseHandler):
    @authorize([Scope.student, Scope.tutor, Scope.instructor])
    async def get(self):
        """
        Returns the premissions of a user
        """
        response = []
        role: Role
        for role in self.user.roles:
            response.append(
                {"lecture_code": role.lecture.code, "scope": role.role.value}
            )
        self.write_json(response)