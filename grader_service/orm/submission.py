# Copyright (c) 2022, TU Wien
# All rights reserved.
# grader service orm
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from grader_service.api.models import submission
from grader_service.orm.base import Base, DeleteState, Serializable


class AutoStatus(StrEnum):
    """Allowed `auto_status` values of a submission"""

    NOT_GRADED = "not_graded"
    PENDING = "pending"
    AUTOMATICALLY_GRADED = "automatically_graded"
    GRADING_FAILED = "grading_failed"


class ManualStatus(StrEnum):
    """Allowed `manual_status` values of a submission"""

    NOT_GRADED = "not_graded"
    MANUALLY_GRADED = "manually_graded"
    BEING_EDITED = "being_edited"


class FeedbackStatus(StrEnum):
    """Allowed `feedback_status` values of a submission"""

    NOT_GENERATED = "not_generated"
    GENERATING = "generating"
    GENERATED = "generated"
    GENERATION_FAILED = "generation_failed"
    FEEDBACK_OUTDATED = "feedback_outdated"


class Submission(Base, Serializable):
    __tablename__ = "submission"
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False)
    auto_status = Column(Enum(AutoStatus), default=AutoStatus.NOT_GRADED, nullable=False)
    manual_status = Column(Enum(ManualStatus), default=ManualStatus.NOT_GRADED, nullable=False)
    score = Column(Float, nullable=True)
    assignid = Column(Integer, ForeignKey("assignment.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    commit_hash = Column(String(length=40), nullable=False)
    feedback_status = Column(
        Enum(FeedbackStatus), default=FeedbackStatus.NOT_GENERATED, nullable=False
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
    logs = relationship(
        "SubmissionLogs",
        back_populates="submission",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    properties = relationship(
        "SubmissionProperties",
        back_populates="submission",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @hybrid_property
    def user_display_name(self) -> str:
        return self.user.display_name

    @property
    def model(self) -> submission.Submission:
        model = submission.Submission(
            id=self.id,
            submitted_at=None if self.date is None else (self.date.isoformat("T", "milliseconds")),
            user_id=self.user_id,
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

    def serialize_with_user(self) -> dict:
        """Serialize the submission with user information.

        Returns:
            dict: The serialized submission data including user information.
        """
        model = self.model.to_dict()
        model["user"] = self.user.serialize()
        return model

    def serialize_with_lectid(self) -> dict:
        """Serialize the submission with lectid.

        Returns:
            dict: The serialized submission data including lectid.
        """
        model = self.model.to_dict()
        model["lectid"] = self.assignment.lectid
        return model
