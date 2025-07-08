# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import json
from datetime import date, datetime, timezone
from typing import Any, Union

from sqlalchemy import DECIMAL, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from grader_service.api.models import assignment
from grader_service.api.models.assignment_settings import AssignmentSettings
from grader_service.orm.base import Base, DeleteState, Serializable


def get_utc_time():
    return datetime.now(tz=timezone.utc)


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


class Assignment(Base, Serializable):
    __tablename__ = "assignment"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    """Name of the assignment"""
    lectid = Column(Integer, ForeignKey("lecture.id"))
    points = Column(DECIMAL(10, 3), nullable=True)
    status = Column(Enum("created", "pushed", "released", "complete"), default="created")
    deleted = Column(Enum(DeleteState), nullable=False, unique=False)
    properties = Column(Text, nullable=True, unique=False)
    created_at = Column(DateTime, default=get_utc_time, nullable=False)
    updated_at = Column(DateTime, default=get_utc_time, onupdate=get_utc_time, nullable=False)
    _settings = Column("settings", Text, server_default="", nullable=False)

    lecture = relationship("Lecture", back_populates="assignments")
    submissions = relationship("Submission", back_populates="assignment")

    @property
    def settings(self) -> AssignmentSettings:
        if self._settings is None:
            return AssignmentSettings()
        return AssignmentSettings.from_dict(json.loads(self._settings))

    @settings.setter
    def settings(self, settings: Union[AssignmentSettings, dict]):
        if isinstance(settings, dict):
            self._settings = json.dumps(settings, default=json_serial)
            return settings
        self._settings = json.dumps(settings.to_dict(), default=json_serial)
        return settings

    def update_settings(self, **kwargs: Any):
        # Update specific fields of the AssignmentSettings object
        settings = self.settings  # Get the current AssignmentSettings object
        for key, value in kwargs.items():
            if key not in AssignmentSettings.openapi_types.keys():
                raise RuntimeError(f"provided key '{key}' is not valid for assignment settings")
            if hasattr(settings, key):  # Ensure the attribute exists on AssignmentSettings
                setattr(settings, key, value)
        self.settings = settings  # Save the updated object back

    @property
    def model(self) -> assignment.Assignment:
        assignment_model = assignment.Assignment(
            id=self.id,
            name=self.name,
            status=self.status,
            points=self.points,
            settings=self.settings,
        )
        return assignment_model
