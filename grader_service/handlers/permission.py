# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

from grader_service.handlers.base_handler import GraderBaseHandler, authorize
from grader_service.orm.takepart import Role, Scope
from grader_service.registry import VersionSpecifier, register_handler


@register_handler(path=r"\/api\/permissions\/?", version_specifier=VersionSpecifier.ALL)
class PermissionHandler(GraderBaseHandler):
    """
    Tornado Handler class for http requests to /permissions.
    """

    @authorize([Scope.student, Scope.tutor, Scope.instructor])
    async def get(self):
        """
        Finds the permissions of a user.
        :return permissions of the user
        """
        response = []
        role: Role
        for role in self.user.roles:
            response.append({"lecture_code": role.lecture.code, "scope": role.role.value})
        self.write_json(response)
