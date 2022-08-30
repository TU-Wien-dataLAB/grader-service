# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import enum
from datetime import datetime

from grader_service.api.models import lecture
from sqlalchemy import Column, Enum, Integer, String, DateTime
from sqlalchemy.orm import relationship

from grader_service.orm.base import Base, DeleteState, Serializable


class LectureState(enum.IntEnum):
    active = 0
    complete = 1


class Lecture(Base, Serializable):
    __tablename__ = "lecture"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=True, unique=False)
    code = Column(String(255), nullable=True, unique=True)
    state = Column(Enum(LectureState), nullable=False, unique=False)
    deleted = Column(Enum(DeleteState), nullable=False, unique=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    assignments = relationship("Assignment", back_populates="lecture")
    roles = relationship("Role", back_populates="lecture")
    groups = relationship("Group", back_populates="lecture")

    @property
    def model(self) -> lecture.Lecture:
        return lecture.Lecture(
            id=self.id,
            name=self.name,
            code=self.code,
            complete=self.state == LectureState.complete,
        )
