# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

from sqlalchemy import Column, LargeBinary, String, Unicode
from sqlalchemy.orm import Session, relationship

from grader_service.api.models import user
from grader_service.auth.crypto import (
    CryptKeeper,
    EncryptionUnavailable,
    InvalidToken,
    decrypt,
    encrypt,
)
from grader_service.orm.base import Base, Serializable
from grader_service.utils import new_token


class User(Base, Serializable):
    __tablename__ = "user"
    name = Column(String(255), primary_key=True)
    display_name = Column(String(255), nullable=False)

    roles = relationship("Role", back_populates="user")
    submissions = relationship("Submission", back_populates="user")
    api_tokens = relationship("APIToken", back_populates="user")
    oauth_codes = relationship("OAuthCode", back_populates="user")

    encrypted_auth_state = Column(LargeBinary)
    cookie_id = Column(Unicode(255), default=new_token, nullable=False, unique=True)
    _auth_refreshed = None

    async def save_auth_state(self, auth_state):
        if auth_state is None:
            self.encrypted_auth_state = None
        else:
            self.encrypted_auth_state = await encrypt(auth_state)
        session: Session = Session.object_session(self)
        session.expire_on_commit = False
        session.commit()

    async def get_auth_state(self):
        """Retrieve and decrypt auth_state for the user"""
        encrypted = self.encrypted_auth_state
        if encrypted is None:
            return None
        try:
            auth_state = await decrypt(encrypted)
        except (ValueError, InvalidToken, EncryptionUnavailable) as e:
            self.log.warning(
                "Failed to retrieve encrypted auth_state for %s because %s", self.name, e
            )
            return
        # loading auth_state
        if auth_state:
            # Crypt has multiple keys, store again with new key for rotation.
            if len(CryptKeeper.instance().keys) > 1:
                await self.save_auth_state(auth_state)
        return auth_state

    def serialize(self):
        return {"name": self.name, "display_name": self.display_name}

    @property
    def model(self) -> user.User:
        return user.User(name=self.name, display_name=self.display_name)
