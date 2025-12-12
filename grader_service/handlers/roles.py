from http import HTTPStatus

from sqlalchemy.orm.exc import ObjectDeletedError
from tornado.escape import json_decode
from tornado.web import HTTPError

from grader_service.handlers.base_handler import GraderBaseHandler, authorize
from grader_service.handlers.handler_utils import parse_ids
from grader_service.orm import User
from grader_service.orm.takepart import Role, Scope
from grader_service.registry import VersionSpecifier, register_handler


@register_handler(r"\/api\/users\/(?P<username>[^\/]+)\/roles\/?", VersionSpecifier.ALL)
class RoleUserHandler(GraderBaseHandler):
    """
    Tornado Handler class for http requests to /user/{username}/roles.
    """

    @authorize([Scope.admin])
    async def get(self, username: str):
        """
        Returns all roles for a specific user.

        :param username: name of the user
        :type username: str
        """
        self.validate_parameters()

        db_user = self.session.query(User).filter_by(name=username).first()
        if db_user is None:
            raise HTTPError(HTTPStatus.NOT_FOUND, reason="User not found")

        roles = self.session.query(Role).filter(Role.user_id == db_user.id).all()

        self.set_status(HTTPStatus.OK)
        self.write_json(roles)


@register_handler(r"\/api\/lectures\/(?P<lecture_id>\d*)\/roles\/?", VersionSpecifier.ALL)
class RoleBaseHandler(GraderBaseHandler):
    """
    Tornado Handler class for http requests to /lectures/{lecture_id}/roles.
    """

    @authorize([Scope.admin])
    async def get(self, lecture_id: int):
        """
        Returns all roles for a specific lecture.

        :param lecture_id: id of the lecture
        :type lecture_id: int
        """
        lecture_id = parse_ids(lecture_id)
        self.validate_parameters()

        roles = self.session.query(Role).filter(Role.lectid == lecture_id).all()

        self.set_status(HTTPStatus.OK)
        self.write_json([r.serialize_with_user() for r in roles])

    @authorize([Scope.admin])
    async def post(self, lecture_id: int):
        """
        Creates or update roles for a specific lecture.

        Request body example:
        {
            "users": [
                { "username": "alice", "role": 0 },
                { "username": "bob", "role": 1 }
            ]
        }

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :raises HTTPError: throws err if one user was not found
        """
        lecture_id = parse_ids(lecture_id)
        self.validate_parameters()
        body = json_decode(self.request.body)

        lecture = self.get_lecture(lecture_id)
        if lecture is None:
            raise HTTPError(HTTPStatus.NOT_FOUND, reason="Lecture not found")

        roles = []
        for user_req in body["users"]:
            user = self.session.query(User).filter(User.name == user_req["username"]).one_or_none()
            if user is None:
                self.session.rollback()
                raise HTTPError(
                    HTTPStatus.NOT_FOUND, reason=f"User {user_req['username']} not found"
                )

            role = (
                self.session.query(Role)
                .filter(Role.user_id == user.id)
                .filter(Role.lectid == lecture_id)
                .one_or_none()
            )
            if role is None:
                role = Role()
                role.user_id = user.id
                role.lectid = lecture_id
                self.session.add(role)
            role.role = user_req["role"]
            roles.append(role)
        self.session.commit()

        self.set_status(HTTPStatus.CREATED)
        self.write_json([r.serialize_with_user() for r in roles])

    @authorize([Scope.admin])
    async def delete(self, lecture_id: int):
        """
        Deletes roles for a specific lecture.

        Query parameter example:
        ?usernames=alice,boby

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :raises HTTPError: if the lecture does not exist, no usernames were provided,
                           or at least one user cannot be found
        """
        lecture_id = parse_ids(lecture_id)
        self.validate_parameters("usernames")
        raw_usernames = self.get_argument("usernames", "")

        try:
            # Roles can not be soft-deleted
            if not self.user.is_admin:
                raise HTTPError(HTTPStatus.FORBIDDEN, reason="Only Admins can delete roles.")

            lecture = self.get_lecture(lecture_id)
            if lecture is None:
                raise HTTPError(HTTPStatus.NOT_FOUND, reason="Lecture not found")

            if len(raw_usernames.strip()) == 0:
                raise HTTPError(HTTPStatus.BAD_REQUEST, reason="usernames cannot be empty")
            usernames = raw_usernames.split(",")

            for username in usernames:
                user = self.session.query(User).filter(User.name == username).one_or_none()
                if user is None:
                    self.session.rollback()
                    raise HTTPError(HTTPStatus.NOT_FOUND, reason=f"User {username} was not found")

                role = (
                    self.session.query(Role)
                    .filter(Role.user_id == user.id)
                    .filter(Role.lectid == lecture_id)
                    .one_or_none()
                )
                if role is not None:
                    self.session.delete(role)
            self.session.commit()
        except ObjectDeletedError:
            raise HTTPError(HTTPStatus.NOT_FOUND, reason="Roles was not found")
        self.write("OK")
