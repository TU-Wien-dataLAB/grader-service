# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import os
from tornado import web
from traitlets import config


class GraderServer(config.LoggingConfigurable, web.Application):
    # As an unmanage jupyter hub service, the application gets these environment variables from the hub
    # see: https://jupyterhub.readthedocs.io/en/stable/reference/services.html#launching-a-hub-managed-service

    def __init__(self, grader_service_dir: str, base_url: str, auth_cls, **kwargs):
        super().__init__(**kwargs)
        self.grader_service_dir = grader_service_dir
        self.base_url = base_url
        self.auth_cls = auth_cls

