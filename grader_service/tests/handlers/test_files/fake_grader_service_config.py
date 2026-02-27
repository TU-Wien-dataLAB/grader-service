# ruff: noqa: F821
"""
Fake grader service configuration file for testing the config endpoint.
This file can be used to test the retrieval of cell timeout configurations
when different timeout values are configured.
"""

from grader_service.autograding.local_grader import LocalAutogradeExecutor

# Test configuration with custom cell timeout values
c.RequestHandlerConfig.autograde_executor_class = LocalAutogradeExecutor

# Custom timeout values that differ from defaults
c.LocalAutogradeExecutor.default_cell_timeout = 200
c.LocalAutogradeExecutor.min_cell_timeout = 20
c.LocalAutogradeExecutor.max_cell_timeout = 3600
