# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from grader_service.orm.base import Base

group_assignment_table = Table('partof', Base.metadata,
                               Column('username', ForeignKey('user.name'),
                                      primary_key=True),
                               Column('group_name', ForeignKey('group.name'),
                                      primary_key=True)
                               )


class Group(Base):
    __tablename__ = "group"
    name = Column(String(255))
    lectid = Column(Integer, ForeignKey("lecture.id"), primary_key=True)

    lecture = relationship("Lecture", back_populates="groups")
    users = relationship("User", secondary=group_assignment_table,
                         back_populates="groups")
