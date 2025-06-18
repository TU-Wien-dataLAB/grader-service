import json
from base64 import decodebytes, encodebytes

from sqlalchemy import TypeDecorator
from sqlalchemy.types import Text
from tornado.log import app_log


class JSONDict(TypeDecorator):
    """Represents an immutable structure as a json-encoded string.

    Usage::

               JSONDict(255)

    """

    impl = Text

    def _json_default(self, obj):
        """encode non-jsonable objects as JSON

        Currently only bytes are supported

        """
        if not isinstance(obj, bytes):
            app_log.warning("Non-jsonable data in user_options: %r; will persist None.", type(obj))
            return None

        return {"__jupyterhub_bytes__": True, "data": encodebytes(obj).decode("ascii")}

    def _object_hook(self, dct):
        """decode non-json objects packed by _json_default"""
        if dct.get("__jupyterhub_bytes__", False):
            return decodebytes(dct["data"].encode("ascii"))
        return dct

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value, default=self._json_default)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value, object_hook=self._object_hook)
        return value


class JSONList(JSONDict):
    """Represents an immutable structure as a json-encoded string (to be used for list type columns).

    Usage::

               JSONList(JSONDict)

    """

    def process_bind_param(self, value, dialect):
        if isinstance(value, list) and value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return []
        else:
            value = json.loads(value)
        return value
