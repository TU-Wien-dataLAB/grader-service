"""Miscellaneous utilities"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
import asyncio
import concurrent.futures
import hashlib
import inspect
import secrets
import uuid
from binascii import b2a_hex
from datetime import datetime, timezone
from hmac import compare_digest
from typing import Any

from tornado.log import app_log


def isoformat(dt):
    """Render a datetime object as an ISO 8601 UTC timestamp

    Naive datetime objects are assumed to be UTC
    """
    # allow null timestamps to remain None without
    # having to check if isoformat should be called
    if dt is None:
        return None
    if dt.tzinfo:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt.isoformat() + "Z"


# Token utilities


def new_token(*args, **kwargs):
    """Generator for new random tokens

    For now, just UUIDs.
    """
    return uuid.uuid4().hex


def hash_token(token, salt=8, rounds=16384, algorithm="sha512"):
    """Hash a token, and return it as `algorithm:salt:hash`.

    If `salt` is an integer, a random salt of that many bytes will be used.
    """
    h = hashlib.new(algorithm)
    if isinstance(salt, int):
        salt = b2a_hex(secrets.token_bytes(salt))
    if isinstance(salt, bytes):
        bsalt = salt
        salt = salt.decode("utf8")
    else:
        bsalt = salt.encode("utf8")
    btoken = token.encode("utf8", "replace")
    h.update(bsalt)
    for i in range(rounds):
        h.update(btoken)
    digest = h.hexdigest()

    return f"{algorithm}:{rounds}:{salt}:{digest}"


def compare_token(compare, token):
    """Compare a token with a hashed token.

    Uses the same algorithm and salt of the hashed token for comparison.
    """
    algorithm, srounds, salt, _ = compare.split(":")
    hashed = hash_token(token, salt=salt, rounds=int(srounds), algorithm=algorithm).encode("utf8")
    compare = compare.encode("utf8")
    if compare_digest(compare, hashed):
        return True
    return False


def url_path_join(*pieces):
    """Join components of url into a relative url.

    Use to prevent double slash when joining subpath. This will leave the
    initial and final / in place.

    Copied from `notebook.utils.url_path_join`.
    """
    initial = pieces[0].startswith("/")
    final = pieces[-1].endswith("/")
    stripped = [s.strip("/") for s in pieces]
    result = "/".join(s for s in stripped if s)

    if initial:
        result = "/" + result
    if final:
        result = result + "/"
    if result == "//":
        result = "/"

    return result


def maybe_future(obj):
    """Return an asyncio Future

    Use instead of gen.maybe_future

    For our compatibility, this must accept:

    - asyncio coroutine (gen.maybe_future doesn't work in tornado < 5)
    - tornado coroutine (asyncio.ensure_future doesn't work)
    - scalar (asyncio.ensure_future doesn't work)
    - concurrent.futures.Future (asyncio.ensure_future doesn't work)
    - tornado Future (works both ways)
    - asyncio Future (works both ways)
    """
    if inspect.isawaitable(obj):
        # already awaitable, use ensure_future
        return asyncio.ensure_future(obj)
    elif isinstance(obj, concurrent.futures.Future):
        return asyncio.wrap_future(obj)
    else:
        # could also check for tornado.concurrent.Future
        # but with tornado >= 5.1 tornado.Future is asyncio.Future
        f = asyncio.Future()
        f.set_result(obj)
        return f


def utcnow(*, with_tz=True):
    """Return utcnow

    with_tz (default): returns tz-aware datetime in UTC

    if with_tz=False, returns UTC timestamp without tzinfo
    (used for most internal timestamp storage because databases often don't preserve tz info)
    """
    now = datetime.now(timezone.utc)
    if not with_tz:
        now = now.replace(tzinfo=None)
    return now


def get_browser_protocol(request):
    """Get the _protocol_ seen by the browser

    Like tornado's _apply_xheaders,
    but in the case of multiple proxy hops,
    use the outermost value (what the browser likely sees)
    instead of the innermost value,
    which is the most trustworthy.

    We care about what the browser sees,
    not where the request actually came from,
    so trusting possible spoofs is the right thing to do.
    """
    headers = request.headers
    # first choice: Forwarded header
    forwarded_header = headers.get("Forwarded")
    if forwarded_header:
        first_forwarded = forwarded_header.split(",", 1)[0].strip()
        fields = {}
        for field in first_forwarded.split(";"):
            key, _, value = field.partition("=")
            fields[key.strip().lower()] = value.strip()
        if "proto" in fields and fields["proto"].lower() in {"http", "https"}:
            return fields["proto"].lower()
        else:
            app_log.warning(f"Forwarded header present without protocol: {forwarded_header}")

    # second choice: X-Scheme or X-Forwarded-Proto
    proto_header = headers.get("X-Scheme", headers.get("X-Forwarded-Proto", None))
    if proto_header:
        proto_header = proto_header.split(",")[0].strip().lower()
        if proto_header in {"http", "https"}:
            return proto_header

    # no forwarded headers
    return request.protocol


def convert_request_to_dict(arguments: dict[str, list[bytes]]) -> dict[str, Any]:
    """
    Converts the arguments obtained from a request to a dict.

    Args:
        arguments: a dictionary of request arguments

    Returns:
        A decoded dict with keys/values extracted from the request's arguments
    """
    args = {}
    for k, values in arguments.items():
        args[k] = values[0].decode()
    return args
