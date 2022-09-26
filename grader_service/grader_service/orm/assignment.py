# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import enum
from datetime import datetime

from grader_service.api.models import assignment
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.orm import relationship

from grader_service.orm.base import Base, DeleteState, Serializable


class AutoGradingBehaviour(enum.Enum):
    unassisted = 0  # assignments are not automatically graded
    auto = 1  # assignments are automatically graded when submitted
    full_auto = 2  # assignments are automatically graded and feedback is generated when submitted


class Assignment(Base, Serializable):
    __tablename__ = "assignment"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    """Name of the assignment"""
    type = Column(Enum("user", "group"), nullable=False, server_default="user")
    """Type of the assignment"""
    lectid = Column(Integer, ForeignKey("lecture.id"))
    duedate = Column(DateTime, nullable=False)
    points = Column(Integer, nullable=True)
    status = Column(
        Enum("created", "pushed", "released", "complete"),
        default="created",
    )
    automatic_grading = Column(Enum(AutoGradingBehaviour), nullable=False)
    deleted = Column(Enum(DeleteState), nullable=False, unique=False)
    max_submissions = Column(Integer, nullable=True, default=None, unique=False)
    allow_files = Column(Boolean, nullable=False, default=False)
    properties = Column(Text, nullable=True, unique=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    lecture = relationship("Lecture", back_populates="assignments")
    submissions = relationship("Submission", back_populates="assignment")

    @property
    def model(self) -> assignment.Assignment:
        assignment_model = assignment.Assignment(
            id=self.id,
            name=self.name,
            due_date=None
            if self.duedate is None
            else (self.duedate.isoformat("T", "milliseconds") + "Z"),
            status=self.status,
            type=self.type,
            points=self.points,
            automatic_grading=self.automatic_grading.name,
            max_submissions=self.max_submissions,
            allow_files=self.allow_files
        )
        return assignment_model
