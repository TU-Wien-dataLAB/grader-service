# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from grader_service.orm.base import Base, Serializable
from grader_service.orm.group import group_assignment_table


class User(Base, Serializable):
    __tablename__ = "user"
    name = Column(String(255), primary_key=True)

    roles = relationship("Role", back_populates="user")
    submissions = relationship("Submission", back_populates="user")
    groups = relationship("Group", secondary=group_assignment_table,
                          back_populates="users")

    def serialize(self):
        return {"name": self.name}
