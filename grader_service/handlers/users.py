from http import HTTPStatus

import tornado
from tornado.escape import json_decode
from tornado.web import HTTPError

from grader_service.api.models.user import User as UserModel
from grader_service.handlers.base_handler import GraderBaseHandler, authorize
from grader_service.orm import User
from grader_service.orm.takepart import Scope
from grader_service.registry import VersionSpecifier, register_handler


@register_handler(r"\/api\/users", VersionSpecifier.ALL)
class UserBaseHandler(GraderBaseHandler):
    """
    Tornado Handler class for http requests to /users.
    """
    @authorize([Scope.admin])
    async def get(self):
        """
        Returns all users.
        """
        self.validate_parameters()
        user = self.session.query(User).filter().all()

        self.set_status(HTTPStatus.OK)
        self.write_json(user)

@register_handler(r"\/api\/users\/(?P<username>[^\/]+)\/?", VersionSpecifier.ALL)
class UserObjectBaseHandler(GraderBaseHandler):
    """
    Tornado Handler class for http requests to /users/{username}.
    """

    @authorize([Scope.admin])
    async def get(self, username: str):
        """
        Returns a specific user.

        :param username: the name of the user.
        :type username: str
        :raises HTTPError: throws err if user was not found
        """
        self.validate_parameters()

        user = self.session.query(User).filter_by(name=username).first()
        if user is None:
            raise HTTPError(HTTPStatus.NOT_FOUND, reason="User not found")

        self.set_status(HTTPStatus.OK)
        self.write_json(user)

    @authorize([Scope.admin])
    async def put(self, username: str):
        """
        Updates a specific user.

        :param username: the name of the user.
        :type username: str
        :raises HTTPError: throws err if user was not found
        """
        self.validate_parameters()
        body = tornado.escape.json_decode(self.request.body)
        user_model = UserModel.from_dict(body)

        user = self.session.query(User).filter_by(name=username).first()
        if user is None:
            raise HTTPError(HTTPStatus.NOT_FOUND, reason="User not found")

        user.display_name = user_model.display_name
        self.session.add(user)
        self.session.commit()

        self.set_status(HTTPStatus.OK)
        self.write_json(user)

    @authorize([Scope.admin])
    async def delete(self, username: str):
        """
        Hard-Deletes a specific user.
        Hard deleting: removes user from datastore.

        :param username: the name of the user.
        :type username: str
        :raises HTTPError:  throws err if user was not found,
                            or user has still submissions,
                            or user has still roles
        """
        self.validate_parameters()

        user = self.session.query(User).filter_by(name=username).first()
        if user is None:
            raise HTTPError(HTTPStatus.NOT_FOUND, reason="User not found")

        if len(user.submissions) > 0:
            msg = "User cannot be deleted: submissions still exist. Delete submissions first!"
            raise HTTPError(HTTPStatus.CONFLICT, reason=msg)
        if len(user.roles) > 0:
            msg = "User cannot be deleted: roles still exist. Delete roles first!"
            raise HTTPError(HTTPStatus.CONFLICT, reason=msg)

        for api_token in user.api_tokens:
            self.session.delete(api_token)
        for oauth_code in user.oauth_codes:
            self.session.delete(oauth_code)
        self.session.delete(user)
        self.session.commit()
