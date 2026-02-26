# Copyright (c) 2026, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import json
import pathlib
from http import HTTPStatus

import pytest
from traitlets.config import Config

from grader_service.server import GraderServer


class TestConfigHandler:
    """Tests for the ConfigHandler endpoint."""

    @pytest.fixture(autouse=False)
    def ensure_app_config(self, app):
        # minimal fixture to ensure app.config and required fields are set for the handler logic
        app.application = app
        # Ensure the required executor class is set for the handler logic
        if not hasattr(app.config, "RequestHandlerConfig"):
            app.config.RequestHandlerConfig = Config()
        if app.config.RequestHandlerConfig.get("autograde_executor_class") is None:
            from grader_service.autograding.local_grader import LocalAutogradeExecutor

            app.config.RequestHandlerConfig.autograde_executor_class = LocalAutogradeExecutor

    def load_fake_config(self, path):
        c = Config()
        with open(path, "r") as f:
            code = f.read()
        exec(code, {"c": c})
        return c

    async def test_get_default_cell_timeout_values(
        self,
        app: GraderServer,
        service_base_url,
        http_server_client,
        default_token,
        default_roles,
        default_user_login,
        ensure_app_config,
    ):
        """Test retrieval of default cell timeout values when no custom config is set."""
        url = service_base_url + "config"

        response = await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
        assert response.code == HTTPStatus.OK
        config_data = json.loads(response.body.decode())

        # Verify default values from LocalAutogradeExecutor
        assert config_data["default_cell_timeout"] == 300
        assert config_data["min_cell_timeout"] == 10
        assert config_data["max_cell_timeout"] == 86400

    async def test_get_custom_cell_timeout_values(
        self,
        app: GraderServer,
        service_base_url,
        http_server_client,
        default_token,
        default_roles,
        default_user_login,
    ):
        """Test retrieval of custom cell timeout values when set in config."""
        # Create custom config
        fake_config_path = (
            pathlib.Path(__file__).parent / "test_files" / "fake_grader_service_config.py"
        )
        fake_config = self.load_fake_config(fake_config_path)
        app.config = fake_config

        url = service_base_url + "config"

        response = await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
        assert response.code == HTTPStatus.OK
        config_data = json.loads(response.body.decode())

        # Verify custom values
        assert config_data["default_cell_timeout"] == 200
        assert config_data["min_cell_timeout"] == 20
        assert config_data["max_cell_timeout"] == 3600

    async def test_get_partial_custom_cell_timeout_values(
        self,
        app: GraderServer,
        service_base_url,
        http_server_client,
        default_token,
        default_roles,
        default_user_login,
        ensure_app_config,
    ):
        """Test retrieval when only some timeout values are customized in config."""
        # Create custom config with only some values set

        custom_config = Config()
        custom_config.LocalAutogradeExecutor.default_cell_timeout = 150
        app.config.merge(custom_config)

        url = service_base_url + "config"

        response = await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
        assert response.code == HTTPStatus.OK
        config_data = json.loads(response.body.decode())

        # Verify the custom value and defaults for others
        assert config_data["default_cell_timeout"] == 150
        assert config_data["min_cell_timeout"] == 10  # default
        assert config_data["max_cell_timeout"] == 86400  # default

    async def test_config_endpoint_requires_authorization(
        self, app: GraderServer, service_base_url, http_server_client
    ):
        """Test that config endpoint requires proper authorization."""
        url = service_base_url + "config"

        # Try without token - should fail
        with pytest.raises(Exception):  # HTTPClientError or similar
            await http_server_client.fetch(url, method="GET")

    async def test_get_config_response_structure(
        self,
        app: GraderServer,
        service_base_url,
        http_server_client,
        default_token,
        default_roles,
        default_user_login,
        ensure_app_config,
    ):
        """Test that config response has the expected structure."""
        url = service_base_url + "config"

        response = await http_server_client.fetch(
            url, method="GET", headers={"Authorization": f"Token {default_token}"}
        )
        assert response.code == HTTPStatus.OK
        config_data = json.loads(response.body.decode())

        # Verify all expected keys are present
        expected_keys = {"default_cell_timeout", "min_cell_timeout", "max_cell_timeout"}
        assert set(config_data.keys()) == expected_keys

        # Verify values are integers
        assert all(isinstance(config_data[key], int) for key in expected_keys)
