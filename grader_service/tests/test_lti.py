# Copyright (c) 2024, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Tests for the multi-platform LTI grade sync plugin, JWKS endpoint, and
the GraderPlugin / PluginManager infrastructure."""

import datetime
import hashlib
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from tornado.web import HTTPError

from grader_service.plugins.base import (
    _PLUGIN_REGISTRY,
    GraderPlugin,
    PluginManager,
    create_plugin_manager,
    register_plugin,
)
from grader_service.plugins.lti import (
    LTIPlatformConfig,
    LTISyncGrades,
    default_lti_username_match,
    default_resolve_lti_urls,
    default_select_systems,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def rsa_private_key():
    """Generate a fresh RSA private key for testing."""
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture()
def private_key_pem(rsa_private_key):
    """PEM-encoded private key string."""
    return rsa_private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()


@pytest.fixture()
def private_key_path(private_key_pem, tmp_path):
    """Write a private key to a temp file and return the path."""
    key_file = tmp_path / "private_key.pem"
    key_file.write_text(private_key_pem)
    return str(key_file)


@pytest.fixture()
def second_private_key_path(tmp_path):
    """Generate a second, distinct private key for multi-platform tests."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    key_file = tmp_path / "private_key_2.pem"
    key_file.write_text(pem)
    return str(key_file)


@pytest.fixture()
def sample_platform(private_key_path):
    """A single :class:`LTIPlatformConfig`."""
    return LTIPlatformConfig(
        name="TestPlatform",
        url_pattern="https://lms.example.com",
        client_id="test-client-id",
        token_url="https://lms.example.com/mod/lti/token.php",
        platform_url="https://lms.example.com",
        private_key_path=private_key_path,
        deployment_id="42",
    )


@pytest.fixture()
def sample_systems_config(private_key_path, second_private_key_path):
    """Two-platform systems config as it would appear in the traitlets config."""
    return [
        {
            "name": "PlatformA",
            "url_pattern": "https://lms-a.example.com",
            "client_id": "platform-a-client-id",
            "token_url": "https://lms-a.example.com/mod/lti/token.php",
            "platform_url": "https://lms-a.example.com",
            "private_key_path": private_key_path,
            "deployment_id": "1",
        },
        {
            "name": "PlatformB",
            "url_pattern": "https://lms-b.example.com",
            "client_id": "platform-b-client-id",
            "token_url": "https://lms-b.example.com/mod/lti/token.php",
            "platform_url": "https://lms-b.example.com",
            "private_key_path": second_private_key_path,
            "deployment_id": "2",
        },
    ]


@pytest.fixture()
def lti_plugin():
    """Create a fresh LTISyncGrades instance (no singleton)."""
    return LTISyncGrades()


# ---------------------------------------------------------------------------
# Plugin infrastructure tests
# ---------------------------------------------------------------------------


class TestGraderPluginBase:
    def test_plugin_requires_name(self):
        """A plugin with an empty name should raise ValueError."""

        class BadPlugin(GraderPlugin):
            name = ""

        with pytest.raises(ValueError, match="non-empty 'name'"):
            BadPlugin()

    def test_plugin_with_name(self):
        class GoodPlugin(GraderPlugin):
            name = "good"

        p = GoodPlugin()
        assert p.name == "good"

    def test_register_plugin_decorator(self):
        """@register_plugin should add the class to the registry."""
        initial_count = len(_PLUGIN_REGISTRY)

        @register_plugin
        class TempPlugin(GraderPlugin):
            name = "temp_test_plugin"

        assert len(_PLUGIN_REGISTRY) == initial_count + 1
        assert _PLUGIN_REGISTRY[-1] is TempPlugin

        # Cleanup
        _PLUGIN_REGISTRY.pop()

    def test_register_plugin_rejects_non_subclass(self):
        with pytest.raises(TypeError, match="subclass of GraderPlugin"):

            @register_plugin
            class NotAPlugin:
                name = "bad"


class TestPluginManager:
    def test_register_and_get(self):
        class DummyPlugin(GraderPlugin):
            name = "dummy"

        manager = PluginManager()
        plugin = DummyPlugin()
        manager.register(plugin)
        assert manager.get("dummy") is plugin
        assert "dummy" in manager
        assert manager["dummy"] is plugin

    def test_get_returns_none_for_unknown(self):
        manager = PluginManager()
        assert manager.get("nonexistent") is None

    def test_len_and_iter(self):
        class P1(GraderPlugin):
            name = "p1"

        class P2(GraderPlugin):
            name = "p2"

        manager = PluginManager()
        manager.register(P1())
        manager.register(P2())
        assert len(manager) == 2
        assert set(manager.names) == {"p1", "p2"}
        assert len(list(manager)) == 2


class TestCreatePluginManager:
    def test_creates_lti_plugin(self):
        """create_plugin_manager should pick up LTISyncGrades via @register_plugin."""
        manager = create_plugin_manager()
        assert "lti" in manager
        lti = manager.get("lti")
        assert isinstance(lti, LTISyncGrades)

    def test_creates_with_config(self, sample_systems_config):
        """create_plugin_manager passes config through to plugins."""
        from traitlets.config import Config

        cfg = Config()
        cfg.LTISyncGrades.systems = sample_systems_config
        cfg.LTISyncGrades.enabled = True

        manager = create_plugin_manager(config=cfg)
        lti = manager.get("lti")
        assert lti.enabled is True
        assert len(lti.systems) == 2


# ---------------------------------------------------------------------------
# LTIPlatformConfig tests
# ---------------------------------------------------------------------------


class TestLTIPlatformConfig:
    def test_kid_generation(self):
        """kid must be sha256(name)[:16]."""
        platform = LTIPlatformConfig(
            name="PlatformA",
            url_pattern="https://lms-a.example.com",
            client_id="x",
            token_url="https://lms-a.example.com/token",
        )
        expected = hashlib.sha256(b"PlatformA").hexdigest()[:16]
        assert platform.kid == expected

    def test_kid_differs_per_platform(self):
        p1 = LTIPlatformConfig(name="A", url_pattern="", client_id="x", token_url="t")
        p2 = LTIPlatformConfig(name="B", url_pattern="", client_id="x", token_url="t")
        assert p1.kid != p2.kid

    def test_get_private_key(self, sample_platform, private_key_pem):
        key = sample_platform.get_private_key()
        assert "BEGIN RSA PRIVATE KEY" in key or "BEGIN PRIVATE KEY" in key

    def test_get_private_key_missing_path(self):
        platform = LTIPlatformConfig(
            name="T", url_pattern="", client_id="x", token_url="t", private_key_path=""
        )
        with pytest.raises(ValueError, match="No private_key_path"):
            platform.get_private_key()

    def test_get_private_key_file_not_found(self):
        platform = LTIPlatformConfig(
            name="T",
            url_pattern="",
            client_id="x",
            token_url="t",
            private_key_path="/nonexistent/key.pem",
        )
        with pytest.raises(FileNotFoundError):
            platform.get_private_key()

    def test_get_public_key(self, sample_platform):
        pub = sample_platform.get_public_key()
        from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey

        assert isinstance(pub, RSAPublicKey)

    def test_token_cache_invalid_initially(self, sample_platform):
        assert not sample_platform.is_token_valid()

    def test_token_cache_valid_after_set(self, sample_platform):
        sample_platform._cached_token = "tok"
        sample_platform._token_ttl = datetime.datetime.now()
        assert sample_platform.is_token_valid()

    def test_token_cache_expired(self, sample_platform):
        sample_platform._cached_token = "tok"
        sample_platform._token_ttl = datetime.datetime.now() - datetime.timedelta(hours=2)
        assert not sample_platform.is_token_valid()

    def test_to_dict(self, sample_platform):
        d = sample_platform.to_dict()
        assert d["name"] == "TestPlatform"
        assert "private_key_path" not in d  # secrets excluded
        assert d["client_id"] == "test-client-id"


# ---------------------------------------------------------------------------
# Default hook tests
# ---------------------------------------------------------------------------


class TestDefaultHooks:
    def test_default_username_match_returns_false(self):
        assert default_lti_username_match({}, {}, None, MagicMock()) is False

    def test_default_select_systems_returns_all(self):
        platforms = [
            LTIPlatformConfig(name="A", url_pattern="", client_id="", token_url=""),
            LTIPlatformConfig(name="B", url_pattern="", client_id="", token_url=""),
        ]
        result = default_select_systems({}, {}, [], platforms)
        assert result == ["A", "B"]

    def test_default_resolve_lti_urls_raises(self):
        platform = LTIPlatformConfig(name="X", url_pattern="", client_id="", token_url="")
        with pytest.raises(NotImplementedError, match="resolve_lti_urls"):
            default_resolve_lti_urls(platform, {}, {}, [])


# ---------------------------------------------------------------------------
# LTISyncGrades – initialisation & platform parsing
# ---------------------------------------------------------------------------


class TestLTISyncGradesInit:
    def test_has_lti_name(self, lti_plugin):
        assert lti_plugin.name == "lti"

    def test_is_grader_plugin(self, lti_plugin):
        assert isinstance(lti_plugin, GraderPlugin)

    def test_parse_systems(self, lti_plugin, sample_systems_config):
        lti_plugin.systems = sample_systems_config
        lti_plugin._parse_systems()
        assert len(lti_plugin.platforms) == 2
        assert lti_plugin.platforms[0].name == "PlatformA"
        assert lti_plugin.platforms[1].name == "PlatformB"

    def test_get_platform_by_name(self, lti_plugin, sample_systems_config):
        lti_plugin.systems = sample_systems_config
        lti_plugin._parse_systems()
        assert lti_plugin.get_platform("PlatformA").client_id == "platform-a-client-id"
        assert lti_plugin.get_platform("PlatformB").client_id == "platform-b-client-id"
        assert lti_plugin.get_platform("NONEXISTENT") is None

    def test_parse_systems_missing_key(self, lti_plugin):
        lti_plugin.systems = [{"name": "bad"}]  # missing client_id, token_url
        with pytest.raises(ValueError, match="Missing required key"):
            lti_plugin._parse_systems()

    def test_lazy_parsing(self, lti_plugin, sample_systems_config):
        lti_plugin.systems = sample_systems_config
        assert lti_plugin._platforms == []
        assert len(lti_plugin.platforms) == 2


# ---------------------------------------------------------------------------
# LTISyncGrades – enable checks
# ---------------------------------------------------------------------------


class TestLTIEnableChecks:
    def test_disabled_by_default(self, lti_plugin):
        assert not lti_plugin.check_if_lti_enabled({}, {}, [], feedback_sync=False)

    def test_enabled_bool(self, lti_plugin):
        lti_plugin.enabled = True
        assert lti_plugin.check_if_lti_enabled({}, {}, [], feedback_sync=False)

    def test_enabled_callable(self, lti_plugin):
        lti_plugin.enabled = lambda lec, assign, subs: lec.get("name") == "test"
        assert lti_plugin.check_if_lti_enabled({"name": "test"}, {}, [], feedback_sync=False)
        assert not lti_plugin.check_if_lti_enabled({"name": "other"}, {}, [], feedback_sync=False)

    def test_feedback_sync_disabled(self, lti_plugin):
        lti_plugin.enabled = True
        lti_plugin.sync_on_feedback = False
        assert not lti_plugin.check_if_lti_enabled({}, {}, [], feedback_sync=True)

    def test_feedback_sync_enabled(self, lti_plugin):
        lti_plugin.enabled = True
        lti_plugin.sync_on_feedback = True
        assert lti_plugin.check_if_lti_enabled({}, {}, [], feedback_sync=True)

    def test_feedback_sync_callable(self, lti_plugin):
        lti_plugin.enabled = True
        lti_plugin.sync_on_feedback = lambda lec, assign, subs: True
        assert lti_plugin.check_if_lti_enabled({}, {}, [], feedback_sync=True)


# ---------------------------------------------------------------------------
# LTISyncGrades – JWKS generation
# ---------------------------------------------------------------------------


class TestJWKS:
    def test_jwks_empty_when_no_systems(self, lti_plugin):
        jwks = lti_plugin.get_jwks()
        assert jwks == {"keys": []}

    def test_jwks_contains_keys(self, lti_plugin, sample_systems_config):
        lti_plugin.systems = sample_systems_config
        lti_plugin._parse_systems()
        jwks = lti_plugin.get_jwks()
        assert len(jwks["keys"]) == 2

        kids = {k["kid"] for k in jwks["keys"]}
        expected_kids = {
            hashlib.sha256(b"PlatformA").hexdigest()[:16],
            hashlib.sha256(b"PlatformB").hexdigest()[:16],
        }
        assert kids == expected_kids

    def test_jwks_key_fields(self, lti_plugin, sample_systems_config):
        lti_plugin.systems = sample_systems_config
        lti_plugin._parse_systems()
        jwks = lti_plugin.get_jwks()
        for key in jwks["keys"]:
            assert key["kty"] == "RSA"
            assert key["alg"] == "RS256"
            assert key["use"] == "sig"
            assert "n" in key
            assert "e" in key
            assert "kid" in key

    def test_jwks_skips_invalid_keys(self, lti_plugin):
        """If a platform's key file is missing, it should be skipped."""
        lti_plugin.systems = [
            {
                "name": "Bad",
                "url_pattern": "",
                "client_id": "x",
                "token_url": "t",
                "private_key_path": "/nonexistent.pem",
            }
        ]
        lti_plugin._parse_systems()
        jwks = lti_plugin.get_jwks()
        assert len(jwks["keys"]) == 0


# ---------------------------------------------------------------------------
# LTISyncGrades – bearer token request
# ---------------------------------------------------------------------------


class TestBearerTokenRequest:
    @pytest.mark.asyncio
    async def test_request_bearer_token(self, sample_platform):
        """Test JWT assertion is created with correct kid and token is returned."""
        plugin = LTISyncGrades()

        mock_response = MagicMock()
        mock_response.body = json.dumps({"access_token": "test-token-123"}).encode()

        with patch("grader_service.plugins.lti.AsyncHTTPClient") as MockClient:
            mock_client = MagicMock()
            mock_client.fetch = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_client

            token = await plugin.request_bearer_token(sample_platform)
            assert token == "test-token-123"

            call_args = mock_client.fetch.call_args
            req = call_args[0][0]
            assert req.url == sample_platform.token_url
            assert req.method == "POST"
            assert "application/x-www-form-urlencoded" in req.headers["Content-Type"]

            import jwt as pyjwt

            body_str = req.body
            if isinstance(body_str, bytes):
                body_str = body_str.decode()
            params = dict(p.split("=", 1) for p in body_str.split("&"))
            assertion = params["client_assertion"]
            header = pyjwt.get_unverified_header(assertion)
            assert header["kid"] == sample_platform.kid
            assert header["alg"] == "RS256"

    @pytest.mark.asyncio
    async def test_request_bearer_token_no_client_id(self):
        plugin = LTISyncGrades()
        platform = LTIPlatformConfig(name="T", url_pattern="", client_id="", token_url="http://x")
        with pytest.raises(HTTPError, match="client_id"):
            await plugin.request_bearer_token(platform)

    @pytest.mark.asyncio
    async def test_request_bearer_token_no_token_url(self):
        plugin = LTISyncGrades()
        platform = LTIPlatformConfig(name="T", url_pattern="", client_id="cid", token_url="")
        with pytest.raises(HTTPError, match="token_url"):
            await plugin.request_bearer_token(platform)


# ---------------------------------------------------------------------------
# LTISyncGrades – grade publish body
# ---------------------------------------------------------------------------


class TestGradePublishBody:
    def test_body_structure(self):
        body = LTISyncGrades.build_grade_publish_body("user123", 85.5, 100.0)
        assert body["userId"] == "user123"
        assert body["scoreGiven"] == 85.5
        assert body["scoreMaximum"] == 100.0
        assert body["activityProgress"] == "Submitted"
        assert body["gradingProgress"] == "FullyGraded"
        assert "timestamp" in body


# ---------------------------------------------------------------------------
# LTISyncGrades – multi-platform sync (integration with mocks)
# ---------------------------------------------------------------------------


def _make_mock_response(body_dict, code=200):
    """Create a mock HTTP response."""
    resp = MagicMock()
    resp.body = json.dumps(body_dict).encode()
    resp.code = code
    return resp


class TestMultiPlatformSync:
    @pytest.mark.asyncio
    async def test_start_no_submissions(self, lti_plugin, sample_systems_config):
        lti_plugin.systems = sample_systems_config
        lti_plugin._parse_systems()
        with pytest.raises(HTTPError, match="No submissions"):
            await lti_plugin.start({}, {}, [])

    @pytest.mark.asyncio
    async def test_start_no_systems(self, lti_plugin):
        lti_plugin.systems = []
        with pytest.raises(HTTPError, match="No LTI systems configured"):
            await lti_plugin.start({}, {}, [{"id": 1}])

    @pytest.mark.asyncio
    async def test_start_selects_platforms(self, lti_plugin, sample_systems_config):
        """Only selected platforms should be synced."""
        lti_plugin.systems = sample_systems_config
        lti_plugin._parse_systems()

        lti_plugin.select_systems_for_sync = lambda lec, assign, subs, platforms: ["PlatformA"]
        lti_plugin.resolve_lti_urls = lambda platform, lec, assign, subs: {
            "lineitems_url": f"https://{platform.name}/lineitems",
            "membership_url": f"https://{platform.name}/members",
        }
        lti_plugin.username_match = lambda member, sub, platform, log: False

        token_resp = _make_mock_response({"access_token": "tok"})
        members_resp = _make_mock_response({"members": []})
        lineitems_resp = _make_mock_response([])

        with patch("grader_service.plugins.lti.AsyncHTTPClient") as MockClient:
            mock_client = MagicMock()
            mock_client.fetch = AsyncMock(side_effect=[token_resp, members_resp, lineitems_resp])
            MockClient.return_value = mock_client

            result = await lti_plugin.start(
                {"id": 1, "name": "Lecture"},
                {"id": 1, "name": "Assignment", "points": 100},
                [{"id": 1, "score": 80, "user": {"name": "alice"}}],
            )

        assert len(result["synced_platforms"]) == 1
        assert result["synced_platforms"][0]["platform"] == "PlatformA"

    @pytest.mark.asyncio
    async def test_full_sync_with_matching(self, private_key_path):
        """End-to-end sync with username matching across a single platform."""
        plugin = LTISyncGrades()
        plugin.systems = [
            {
                "name": "TestLMS",
                "url_pattern": "https://lms.example.com",
                "client_id": "cid",
                "token_url": "https://lms.example.com/token",
                "private_key_path": private_key_path,
            }
        ]
        plugin._parse_systems()

        plugin.resolve_lti_urls = lambda platform, lec, assign, subs: {
            "lineitems_url": "https://lms.example.com/lineitems",
            "membership_url": "https://lms.example.com/members",
        }

        def match_fn(member, submission, platform, log):
            return member.get("name") == submission.get("user", {}).get("name")

        plugin.username_match = match_fn

        token_resp = _make_mock_response({"access_token": "tok"})
        members_resp = _make_mock_response(
            {
                "members": [
                    {"user_id": "lti-alice", "name": "alice"},
                    {"user_id": "lti-bob", "name": "bob"},
                ]
            }
        )
        lineitems_resp = _make_mock_response(
            [{"id": "https://lms.example.com/lineitem/1", "label": "HW1"}]
        )
        score_resp = _make_mock_response({})

        with patch("grader_service.plugins.lti.AsyncHTTPClient") as MockClient:
            mock_client = MagicMock()
            mock_client.fetch = AsyncMock(
                side_effect=[token_resp, members_resp, lineitems_resp, score_resp]
            )
            MockClient.return_value = mock_client

            result = await plugin.start(
                {"id": 1, "name": "Lecture"},
                {"id": 1, "name": "HW1", "points": 100},
                [{"id": 1, "score": 95, "user": {"name": "alice"}}],
            )

        platform_result = result["synced_platforms"][0]
        assert platform_result["platform"] == "TestLMS"
        assert platform_result["syncable_users"] == 1
        assert platform_result["synced_user"] == 1

    @pytest.mark.asyncio
    async def test_sync_creates_lineitem_when_missing(self, private_key_path):
        """When no matching lineitem exists, one should be created."""
        plugin = LTISyncGrades()
        plugin.systems = [
            {
                "name": "TestLMS",
                "url_pattern": "https://lms.example.com",
                "client_id": "cid",
                "token_url": "https://lms.example.com/token",
                "private_key_path": private_key_path,
            }
        ]
        plugin._parse_systems()
        plugin.resolve_lti_urls = lambda platform, lec, assign, subs: {
            "lineitems_url": "https://lms.example.com/lineitems",
            "membership_url": "https://lms.example.com/members",
        }
        plugin.username_match = lambda m, s, p, log: m.get("name") == s.get("user", {}).get("name")

        token_resp = _make_mock_response({"access_token": "tok"})
        members_resp = _make_mock_response({"members": [{"user_id": "lti-alice", "name": "alice"}]})
        lineitems_resp = _make_mock_response([])
        create_lineitem_resp = _make_mock_response(
            {"id": "https://lms.example.com/lineitem/new", "label": "NewAssignment"}
        )
        score_resp = _make_mock_response({})

        with patch("grader_service.plugins.lti.AsyncHTTPClient") as MockClient:
            mock_client = MagicMock()
            mock_client.fetch = AsyncMock(
                side_effect=[
                    token_resp,
                    members_resp,
                    lineitems_resp,
                    create_lineitem_resp,
                    score_resp,
                ]
            )
            MockClient.return_value = mock_client

            result = await plugin.start(
                {"id": 1, "name": "Lecture"},
                {"id": 1, "name": "NewAssignment", "points": 50},
                [{"id": 1, "score": 40, "user": {"name": "alice"}}],
            )

        fetch_calls = mock_client.fetch.call_args_list
        create_call = fetch_calls[3]  # 4th call = create lineitem
        assert create_call[0][0].method == "POST"
        assert "lineitems" in create_call[0][0].url

        platform_result = result["synced_platforms"][0]
        assert platform_result["synced_user"] == 1

    @pytest.mark.asyncio
    async def test_multi_platform_sync(self, private_key_path, second_private_key_path):
        """Sync to two platforms simultaneously."""
        plugin = LTISyncGrades()
        plugin.systems = [
            {
                "name": "Platform1",
                "url_pattern": "https://p1.example.com",
                "client_id": "cid1",
                "token_url": "https://p1.example.com/token",
                "private_key_path": private_key_path,
            },
            {
                "name": "Platform2",
                "url_pattern": "https://p2.example.com",
                "client_id": "cid2",
                "token_url": "https://p2.example.com/token",
                "private_key_path": second_private_key_path,
            },
        ]
        plugin._parse_systems()

        plugin.resolve_lti_urls = lambda platform, lec, assign, subs: {
            "lineitems_url": f"https://{platform.name.lower()}.example.com/lineitems",
            "membership_url": f"https://{platform.name.lower()}.example.com/members",
        }
        plugin.username_match = lambda m, s, p, log: False

        token_resp = _make_mock_response({"access_token": "tok"})
        members_resp = _make_mock_response({"members": []})
        lineitems_resp = _make_mock_response([])

        with patch("grader_service.plugins.lti.AsyncHTTPClient") as MockClient:
            mock_client = MagicMock()
            mock_client.fetch = AsyncMock(
                side_effect=[
                    token_resp,
                    members_resp,
                    lineitems_resp,
                    token_resp,
                    members_resp,
                    lineitems_resp,
                ]
            )
            MockClient.return_value = mock_client

            result = await plugin.start(
                {"id": 1, "name": "Lecture"},
                {"id": 1, "name": "HW", "points": 100},
                [{"id": 1, "score": 80, "user": {"name": "x"}}],
            )

        assert len(result["synced_platforms"]) == 2
        names = {r["platform"] for r in result["synced_platforms"]}
        assert names == {"Platform1", "Platform2"}

    @pytest.mark.asyncio
    async def test_platform_error_does_not_stop_others(
        self, private_key_path, second_private_key_path
    ):
        """If one platform fails, others should still be synced."""
        plugin = LTISyncGrades()
        plugin.systems = [
            {
                "name": "FailPlatform",
                "url_pattern": "https://fail.example.com",
                "client_id": "cid",
                "token_url": "https://fail.example.com/token",
                "private_key_path": private_key_path,
            },
            {
                "name": "OKPlatform",
                "url_pattern": "https://ok.example.com",
                "client_id": "cid",
                "token_url": "https://ok.example.com/token",
                "private_key_path": second_private_key_path,
            },
        ]
        plugin._parse_systems()

        def resolve_urls(platform, lec, assign, subs):
            if platform.name == "FailPlatform":
                raise RuntimeError("Simulated failure")
            return {
                "lineitems_url": "https://ok.example.com/lineitems",
                "membership_url": "https://ok.example.com/members",
            }

        plugin.resolve_lti_urls = resolve_urls
        plugin.username_match = lambda m, s, p, log: False

        async def mock_fetch(request):
            url = request.url if hasattr(request, "url") else str(request)
            method = request.method if hasattr(request, "method") else "GET"
            if "token" in url:
                return _make_mock_response({"access_token": "tok"})
            elif "members" in url:
                return _make_mock_response({"members": []})
            elif "lineitems" in url:
                if method == "POST":
                    return _make_mock_response(
                        {"id": "https://ok.example.com/lineitem/1", "label": "HW"}
                    )
                return _make_mock_response(
                    [{"id": "https://ok.example.com/lineitem/1", "label": "HW"}]
                )
            return _make_mock_response({})

        with patch("grader_service.plugins.lti.AsyncHTTPClient") as MockClient:
            mock_client = MagicMock()
            mock_client.fetch = AsyncMock(side_effect=mock_fetch)
            MockClient.return_value = mock_client

            result = await plugin.start(
                {"id": 1, "name": "Lecture"},
                {"id": 1, "name": "HW", "points": 100},
                [{"id": 1, "score": 80, "user": {"name": "x"}}],
            )

        assert len(result["synced_platforms"]) == 2
        fail_result = next(r for r in result["synced_platforms"] if r["platform"] == "FailPlatform")
        ok_result = next(r for r in result["synced_platforms"] if r["platform"] == "OKPlatform")
        assert "error" in fail_result
        assert "error" not in ok_result

    @pytest.mark.asyncio
    async def test_token_caching_per_platform(self, private_key_path, second_private_key_path):
        """Each platform should have its own token cache."""
        plugin = LTISyncGrades()
        plugin.systems = [
            {
                "name": "P1",
                "url_pattern": "",
                "client_id": "c1",
                "token_url": "https://p1/token",
                "private_key_path": private_key_path,
            },
            {
                "name": "P2",
                "url_pattern": "",
                "client_id": "c2",
                "token_url": "https://p2/token",
                "private_key_path": second_private_key_path,
            },
        ]
        plugin._parse_systems()

        p1 = plugin.get_platform("P1")
        p2 = plugin.get_platform("P2")

        p1._cached_token = "tok-p1"
        p1._token_ttl = datetime.datetime.now()

        assert p1.is_token_valid()
        assert not p2.is_token_valid()


# ---------------------------------------------------------------------------
# JWKS Handler test
# ---------------------------------------------------------------------------


class TestJWKSHandler:
    """Test the JWKS endpoint handler."""

    @pytest.mark.asyncio
    async def test_jwks_handler_response(self, sample_systems_config):
        """The handler should return a valid JWKS JSON."""
        from grader_service.handlers.lti import LTIJWKSHandler

        # Create a real LTI plugin instance and put it in a PluginManager
        lti_plugin = LTISyncGrades()
        lti_plugin.systems = sample_systems_config
        lti_plugin._parse_systems()

        manager = PluginManager()
        manager.register(lti_plugin)

        # Mock the handler and its application
        handler = MagicMock(spec=LTIJWKSHandler)
        handler.write = MagicMock()
        handler.set_header = MagicMock()
        handler.application = MagicMock()
        handler.application.plugin_manager = manager

        await LTIJWKSHandler.get(handler)

        handler.set_header.assert_any_call("Content-Type", "application/json")
        handler.set_header.assert_any_call("Cache-Control", "public, max-age=3600")

        written_data = handler.write.call_args[0][0]
        jwks = json.loads(written_data)
        assert "keys" in jwks
        assert len(jwks["keys"]) == 2


# ---------------------------------------------------------------------------
# Celery task compatibility test
# ---------------------------------------------------------------------------


class TestCeleryTaskCompat:
    """Verify the celery lti_sync_task still works with the plugin manager."""

    @pytest.mark.asyncio
    async def test_lti_plugin_enable_checks(self):
        """When disabled, the plugin should report not enabled."""
        plugin = LTISyncGrades()
        plugin.enabled = False

        assert not plugin.check_if_lti_enabled({}, {}, [], feedback_sync=True)
        assert not plugin.check_if_lti_enabled({}, {}, [], feedback_sync=False)

    @pytest.mark.asyncio
    async def test_lti_plugin_start_returns_dict(self, private_key_path):
        """When enabled, start() returns the new multi-platform format."""
        plugin = LTISyncGrades()
        plugin.enabled = True
        plugin.systems = [
            {
                "name": "LMS",
                "url_pattern": "",
                "client_id": "cid",
                "token_url": "https://lms.example.com/token",
                "private_key_path": private_key_path,
            }
        ]
        plugin._parse_systems()
        plugin.resolve_lti_urls = lambda p, lect, assign, subs: {
            "lineitems_url": "https://lms.example.com/lineitems",
            "membership_url": "https://lms.example.com/members",
        }
        plugin.username_match = lambda m, s, p, log: False

        token_resp = _make_mock_response({"access_token": "tok"})
        members_resp = _make_mock_response({"members": []})
        lineitems_resp = _make_mock_response([])

        with patch("grader_service.plugins.lti.AsyncHTTPClient") as MockClient:
            mock_client = MagicMock()
            mock_client.fetch = AsyncMock(side_effect=[token_resp, members_resp, lineitems_resp])
            MockClient.return_value = mock_client

            result = await plugin.start(
                {"id": 1, "name": "Lecture"},
                {"id": 1, "name": "HW", "points": 100},
                [{"id": 1, "score": 80, "user": {"name": "x"}}],
            )

        assert "synced_platforms" in result
        assert isinstance(result["synced_platforms"], list)
