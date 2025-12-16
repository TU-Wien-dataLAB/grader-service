from sqlalchemy import Column, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from grader_service.orm.base import Base, Serializable


class SubmissionProperties(Base, Serializable):
    __tablename__ = "submission_properties"
    sub_id = Column(Integer, ForeignKey("submission.id", ondelete="CASCADE"), primary_key=True)
    properties = Column(Text, nullable=True)

    submission = relationship("Submission", back_populates="properties")
