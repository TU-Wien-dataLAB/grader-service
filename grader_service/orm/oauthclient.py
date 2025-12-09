from sqlalchemy import Column, Integer, Unicode
from sqlalchemy.orm import relationship

from grader_service.orm.api_token import APIToken
from grader_service.orm.base import Base
from grader_service.orm.oauthcode import OAuthCode


class OAuthClient(Base):
    __tablename__ = "oauth_client"
    id = Column(Integer, primary_key=True, autoincrement=True)
    identifier = Column(Unicode(255), unique=True)
    description = Column(Unicode(1023))
    secret = Column(Unicode(255))
    redirect_uri = Column(Unicode(1023))

    @property
    def client_id(self):
        return self.identifier

    access_tokens = relationship(
        APIToken, back_populates="oauth_client", cascade="all, delete-orphan"
    )
    codes = relationship(OAuthCode, back_populates="client", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<{self.__class__.__name__}(identifier={self.identifier!r})>"
