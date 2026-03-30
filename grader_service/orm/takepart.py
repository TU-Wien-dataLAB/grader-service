# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import enum

from sqlalchemy import Column, Enum, ForeignKey, Integer
from sqlalchemy.orm import relationship

from grader_service.orm.base import Base, Serializable


class Scope(enum.IntEnum):
    student = 0
    tutor = 1
    instructor = 2
    admin = 3


class Role(Base, Serializable):
    __tablename__ = "takepart"
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), primary_key=True)
    lectid = Column(Integer, ForeignKey("lecture.id", ondelete="CASCADE"), primary_key=True)
    role = Column(Enum(Scope), nullable=False)

    lecture = relationship("Lecture", back_populates="roles")
    user = relationship("User", back_populates="roles")

    def serialize(self):
        return {"user_id": self.user_id, "lectid": self.lectid, "role": self.role}

    def serialize_with_user(self) -> dict:
        """Serialize the role with user information.

        Returns:
            dict: The serialized role data including user information.
        """
        model = self.serialize()
        model["user"] = self.user.serialize()
        return model
