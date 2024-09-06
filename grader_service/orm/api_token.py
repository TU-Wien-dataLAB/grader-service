from datetime import timedelta, datetime

from sqlalchemy import or_, Column, Integer, ForeignKey, Unicode, DateTime, \
    inspect
from sqlalchemy.orm import relationship
from sqlalchemy.orm.strategy_options import joinedload
from tornado.log import app_log

from grader_service.orm import Base, Role
from grader_service.orm.json_util import JSONList
from grader_service.utils import utcnow, hash_token, compare_token, new_token


class Expiring:
    """Mixin for expiring entries

    Subclass must define at least expires_at property,
    which should be unix timestamp or datetime object
    """

    now = utcnow  # function, must return float timestamp or datetime
    expires_at = None  # must be defined

    @property
    def expires_in(self):
        """Property returning expiration in seconds from now

        or None
        """
        if self.expires_at:
            delta = self.expires_at - self.now()
            if isinstance(delta, timedelta):
                delta = delta.total_seconds()
            return delta
        else:
            return None

    @classmethod
    def purge_expired(cls, db):
        """Purge expired API Tokens from the database"""
        now = cls.now()
        deleted = False
        for obj in (
                db.query(cls).filter(
                    cls.expires_at is not None).filter(cls.expires_at < now)
        ):
            app_log.debug("Purging expired %s", obj)
            deleted = True
            db.delete(obj)
        if deleted:
            db.commit()


class Hashed(Expiring):
    """Mixin for tables with hashed tokens"""

    prefix_length = 4
    algorithm = "sha512"
    rounds = 16384
    salt_bytes = 8
    min_length = 8

    # values to use for internally generated tokens,
    # which have good entropy as UUIDs
    generated = True
    generated_salt_bytes = 8
    generated_rounds = 1

    @property
    def token(self):
        raise AttributeError("token is write-only")

    @token.setter
    def token(self, token):
        """Store the hashed value and prefix for a token"""
        self.prefix = token[: self.prefix_length]
        if self.generated:
            # Generated tokens are UUIDs, which have sufficient entropy on their own
            # and don't need salt & hash rounds.
            # ref: https://security.stackexchange.com/a/151262/155114
            rounds = self.generated_rounds
            salt_bytes = self.generated_salt_bytes
        else:
            rounds = self.rounds
            salt_bytes = self.salt_bytes
        self.hashed = hash_token(
            token, rounds=rounds, salt=salt_bytes, algorithm=self.algorithm
        )

    def match(self, token):
        """Is this my token?"""
        return compare_token(self.hashed, token)

    @classmethod
    def check_token(cls, db, token):
        """Check if a token is acceptable"""
        if len(token) < cls.min_length:
            raise ValueError(
                "Tokens must be at least %i characters, got %r"
                % (cls.min_length, token)
            )
        found = cls.find(db, token)
        if found:
            raise ValueError(
                "Collision on token: %s..." % token[: cls.prefix_length])

    @classmethod
    def find_prefix(cls, db, token):
        """Start the query for matching token.

        Returns an SQLAlchemy query already filtered by prefix-matches.

        .. versionchanged:: 1.2

            Excludes expired matches.
        """
        prefix = token[: cls.prefix_length]
        # since we can't filter on hashed values, filter on prefix
        # so we aren't comparing with all tokens
        prefix_match = db.query(cls).filter_by(prefix=prefix)
        prefix_match = prefix_match.filter(
            or_(cls.expires_at is None, cls.expires_at >= cls.now())
        )
        return prefix_match

    @classmethod
    def find(cls, db, token):
        """Find a token object by value.

        Returns None if not found.

        `kind='user'` only returns API tokens for users
        """
        prefix_match = cls.find_prefix(db, token).options(
            joinedload(cls.user)
        )

        for orm_token in prefix_match:
            if orm_token.match(token):
                return orm_token


class APIToken(Hashed, Base):
    """An API token"""

    __tablename__ = 'api_token'

    username = Column(
        Unicode,
        ForeignKey('user.name', ondelete="CASCADE"),
        nullable=True,
    )

    user = relationship("User", back_populates="api_tokens")
    oauth_client = relationship("OAuthClient", back_populates="access_tokens")

    id = Column(Integer, primary_key=True)
    hashed = Column(Unicode(255), unique=True)
    prefix = Column(Unicode(16), index=True)

    @property
    def api_id(self):
        return 'a%i' % self.id

    @property
    def owner(self):
        return self.user

    # added in 2.0
    client_id = Column(
        Unicode(255),
        ForeignKey(
            'oauth_client.identifier',
            ondelete='CASCADE',
        ),
    )

    # FIXME: refresh_tokens not implemented
    # should be a relation to another token table
    # refresh_token = Column(
    #     Integer,
    #     ForeignKey('refresh_tokens.id', ondelete="CASCADE"),
    #     nullable=True,
    # )

    # the browser session id associated with a given token,
    # if issued during oauth to be stored in a cookie
    session_id = Column(Unicode(255), nullable=True)

    # token metadata for bookkeeping
    now = datetime.utcnow  # for expiry
    created = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, default=None, nullable=True)
    last_activity = Column(DateTime)
    note = Column(Unicode(1023))
    scopes = Column(JSONList, default=[])

    def __repr__(self):
        kind = 'user'
        name = self.user.name
        return "<{cls}('{pre}...', {kind}='{name}', client_id={client_id!r})>".format(
            cls=self.__class__.__name__,
            pre=self.prefix,
            kind=kind,
            name=name,
            client_id=self.client_id,
        )

    @classmethod
    def find(cls, db, token):
        """Find a token object by value.

        Returns None if not found.

        """
        prefix_match = cls.find_prefix(db, token)
        prefix_match = prefix_match.filter(cls.username is not None)
        for orm_token in prefix_match:
            if orm_token.match(token):
                if not orm_token.client_id:
                    app_log.warning(
                        "Deleting stale oauth token for %s with no client",
                        orm_token.user and orm_token.user.name,
                    )
                    db.delete(orm_token)
                    db.commit()
                    return
                return orm_token

    @classmethod
    def new(
            cls,
            token=None,
            *,
            user=None,
            scopes=None,
            note='',
            generated=True,
            session_id=None,
            expires_in=None,
            client_id=None,
            oauth_client=None,
            return_orm=False,
    ):
        """Generate a new API token for a user"""
        assert user
        db = inspect(user).session
        if token is None:
            token = new_token()
            # Don't need hash + salt rounds on generated tokens,
            # which already have good entropy
            generated = True
        else:
            cls.check_token(db, token)

        # Avoid circular import
        from .oauthclient import OAuthClient

        if oauth_client is None:
            # lookup oauth client by identifier
            if client_id is None:
                # default: global 'grader' client
                client_id = "grader"
            oauth_client = db.query(OAuthClient).filter_by(
                identifier=client_id).one()
        if client_id is None:
            client_id = oauth_client.identifier

        # two stages to ensure orm_token.generated has been set
        # before token setter is called
        orm_token = cls(
            generated=generated,
            note=note or '',
            client_id=client_id,
            session_id=session_id,
            scopes=scopes if scopes else [],
        )
        db.add(orm_token)
        orm_token.token = token

        assert user.name is not None
        orm_token.user = user
        if expires_in is not None:
            orm_token.expires_at = cls.now() + timedelta(seconds=expires_in)

        db.commit()
        return token

