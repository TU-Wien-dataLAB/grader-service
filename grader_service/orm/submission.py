# Copyright (c) 2022, TU Wien
# All rights reserved.
# grader service orm
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from grader_service.api.models import submission
from grader_service.orm.base import Base, DeleteState, Serializable


class Submission(Base, Serializable):
    __tablename__ = "submission"
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False)
    auto_status = Column(
        Enum("pending", "not_graded", "automatically_graded", "grading_failed"),
        default="not_graded",
        nullable=False,
    )
    manual_status = Column(Enum("not_graded", "manually_graded", "being_edited"))
    score = Column(Float, nullable=True)
    assignid = Column(Integer, ForeignKey("assignment.id"))
    username = Column(String(255), ForeignKey("user.name"))
    commit_hash = Column(String(length=40), nullable=False)
    feedback_status = Column(
        Enum("not_generated", "generating", "generated", "generation_failed", "feedback_outdated"),
        default="not_generated",
        nullable=False,
    )
    deleted = Column(Enum(DeleteState), nullable=False, unique=False, default=DeleteState.active)
    edited = Column(Boolean, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC), nullable=False
    )
    grading_score = Column(Float, nullable=False)
    score_scaling = Column(Float, server_default="1.0", nullable=False)

    assignment = relationship("Assignment", back_populates="submissions")
    user = relationship("User", back_populates="submissions")
    logs = relationship("SubmissionLogs", back_populates="submission", uselist=False)
    properties = relationship("SubmissionProperties", back_populates="submission", uselist=False)

    @hybrid_property
    def user_display_name(self):
        if self.user is None:
            return self.username
        return self.user.display_name

    @property
    def model(self) -> submission.Submission:
        model = submission.Submission(
            id=self.id,
            submitted_at=None if self.date is None else (self.date.isoformat("T", "milliseconds")),
            username=self.username,
            user_display_name=self.user_display_name,
            auto_status=self.auto_status,
            manual_status=self.manual_status,
            score_scaling=self.score_scaling,
            grading_score=self.grading_score,
            score=self.score,
            assignid=self.assignid,
            commit_hash=self.commit_hash,
            feedback_status=self.feedback_status,
            edited=self.edited,
        )
        return model
