from sqlalchemy import Column, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from grader_service.orm.base import Base, Serializable


class SubmissionLogs(Base, Serializable):
    __tablename__ = "submission_logs"
    sub_id = Column(Integer, ForeignKey("submission.id"), primary_key=True)
    logs = Column(Text, nullable=True)

    submission = relationship("Submission", back_populates="logs")
