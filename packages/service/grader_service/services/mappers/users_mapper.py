from grader_service.orm import User
from grader_service.api.models.user import User as UserDto


def to_user_dto(user: User):
    return UserDto(user.id, user.name, user.display_name)
