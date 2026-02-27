# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

# Import plugin modules so that @register_plugin decorators execute and
# populate the plugin registry before create_plugin_manager() is called.
from grader_service.plugins import lti  # noqa: F401
from grader_service.plugins.base import (
    GraderPlugin,
    PluginManager,
    create_plugin_manager,
    register_plugin,
)

__all__ = ["GraderPlugin", "PluginManager", "create_plugin_manager", "register_plugin", "lti"]
