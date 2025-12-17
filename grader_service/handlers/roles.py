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

        lecture = self.get_lecture(lecture_id)
        if lecture is None:
            raise HTTPError(HTTPStatus.NOT_FOUND, reason="Lecture not found")

        roles = self.session.query(Role).filter(Role.lectid == lecture_id).all()

        self.set_status(HTTPStatus.OK)
        self.write_json([r.serialize_with_user() for r in roles])

    @authorize([Scope.admin])
    async def post(self, lecture_id: int):
        """
        Creates or updates roles for a specific lecture.

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
        This operation is atomic. If any error occurs (e.g. user not found,
        role not found, or concurrent modification), no changes are persisted
        to the database.

        Query parameter example:
        ?usernames=alice,boby

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :raises HTTPError:
            - 400 BAD_REQUEST:
                If the "usernames" parameter is missing or empty.
            - 403 FORBIDDEN:
                If the caller is not an administrator.
            - 404 NOT_FOUND:
                If the lecture does not exist, a user does not exist,
                or a role for a given user and lecture does not exist.
            - 409 CONFLICT:
                If a role was concurrently modified or deleted during the operation
                (ObjectDeletedError).
            - 500 INTERNAL_SERVER_ERROR:
                For unexpected errors. In all cases, the transaction is rolled back
                and no partial changes are persisted.
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

            roles_to_delete = []
            for username in usernames:
                user = self.session.query(User).filter(User.name == username).one_or_none()
                if user is None:
                    raise HTTPError(HTTPStatus.NOT_FOUND, reason=f"User {username} was not found")

                role = (
                    self.session.query(Role)
                    .filter(Role.user_id == user.id)
                    .filter(Role.lectid == lecture_id)
                    .one_or_none()
                )
                if role is None:
                    raise HTTPError(
                        HTTPStatus.NOT_FOUND, reason=f"Role for user {username} was not found"
                    )
                roles_to_delete.append(role)

            for role in roles_to_delete:
                self.session.delete(role)
            self.session.commit()
            self.write("OK")
        except ObjectDeletedError:
            self.session.rollback()
            raise HTTPError(HTTPStatus.CONFLICT, reason="Role was modified or deleted concurrently")
        except Exception:
            self.session.rollback()
            raise
