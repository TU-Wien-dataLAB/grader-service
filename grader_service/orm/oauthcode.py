from datetime import datetime, timezone

from sqlalchemy import Column, ForeignKey, Integer, Unicode, or_
from sqlalchemy.orm import joinedload, relationship

from grader_service.orm.base import Base
from grader_service.orm.json_util import JSONList


class OAuthCode(Base):
    __tablename__ = "oauth_code"
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Unicode(255), ForeignKey("oauth_client.identifier", ondelete="CASCADE"))
    client = relationship("OAuthClient", back_populates="codes")
    code = Column(Unicode(36))
    expires_at = Column(Integer)
    redirect_uri = Column(Unicode(1023))
    session_id = Column(Unicode(255))
    # state = Column(Unicode(1023))
    username = Column(Integer, ForeignKey("user.name", ondelete="CASCADE"))
    user = relationship("User", back_populates="oauth_codes")

    scopes = Column(JSONList, default=[])

    @staticmethod
    def now():
        return datetime.now(timezone.utc).timestamp()

    @classmethod
    def find(cls, db, code):
        return (
            db.query(cls)
            .filter(cls.code == code)
            .filter(or_(cls.expires_at is None, cls.expires_at >= cls.now()))
            .options(
                # load user with the code
                joinedload(cls.user, innerjoin=True)
            )
            .first()
        )

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id}, client_id={self.client_id!r})>"
