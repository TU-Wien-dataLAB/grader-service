# Copyright (c) 2026, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from traitlets.config import Config

from grader_service import GraderService
from grader_service.autograding.celery.app import CeleryApp
from grader_service.autograding.celery.tasks import (
    autograde_task,
    generate_feedback_task,
    lti_sync_task,
)
from grader_service.autograding.local_feedback import LocalFeedbackExecutor
from grader_service.handlers.base_handler import RequestHandlerConfig
from grader_service.orm import Submission
from grader_service.orm.submission import FeedbackStatus
from grader_service.tests.handlers.db_util import insert_submission

_lti_sync_result = {
    "synced_platforms": [
        {"platform": "Foo Grader Service", "syncable_users": 42, "synced_user": 42}
    ]
}


@pytest.fixture(scope="function")
def celery_app(app, sql_alchemy_sessionmaker):
    """Mocks CeleryApp instance's plugin manager, initializes GraderService with temp dir"""
    # The following line is necessary for the generate_feedback_task:
    GraderService.grader_service_dir = app.grader_service_dir
    # ...and these two - for the autograde_task:
    grader_service = GraderService.instance()
    grader_service.grader_service_dir = app.grader_service_dir

    mock_plugin = AsyncMock()
    mock_plugin.check_if_lti_enabled.return_value = True
    mock_plugin.start.return_value = _lti_sync_result
    plugin_manager = MagicMock()
    plugin_manager.get.return_value = mock_plugin
    celery_instance = CeleryApp(config=Config(grader_service_dir=app.grader_service_dir))
    celery_instance._plugin_manager = plugin_manager
    with patch.object(CeleryApp, "instance", return_value=celery_instance):
        yield


def test_celery_autograde_task_runs_successfully(sql_alchemy_sessionmaker, celery_app):
    """Test that autograde_task runs without errors with valid inputs."""
    session = sql_alchemy_sessionmaker()
    submission = insert_submission(session.get_bind())
    autograde_task.request.id = "test-task-id"
    autograde_task._sessions = {"test-task-id": session}

    # Mock the actual autograding executor call - this is tested elsewhere
    with (
        patch.object(
            RequestHandlerConfig.instance().autograde_executor_class, "start", return_value=None
        ) as autograding_mock,
        patch.object(autograde_task.log, "info", return_value=MagicMock()),
    ):
        autograde_task.run(
            lecture_id=submission.assignment.lectid,
            assignment_id=submission.assignid,
            sub_id=submission.id,
        )

        autograding_mock.assert_called_once()
        assert autograde_task.log.info.call_count == 2

        # Cleanup
        autograde_task._sessions["test-task-id"].close()


def test_celery_autograde_task_invalid_submission_id(sql_alchemy_sessionmaker, celery_app):
    """Test that autograde_task raises error for non-existent submission."""
    session = sql_alchemy_sessionmaker()
    autograde_task.request.id = "test-task-id"
    autograde_task._sessions = {"test-task-id": session}

    with pytest.raises(ValueError, match="Submission not found"):
        autograde_task.run(
            lecture_id=1,
            assignment_id=1,
            sub_id=99999,  # Non-existent submission
        )

    autograde_task._sessions["test-task-id"].close()


def test_celery_autograde_task_mismatched_ids(sql_alchemy_sessionmaker, celery_app):
    """Test that autograde_task raises error when IDs of lecture and submission don't match."""
    session = sql_alchemy_sessionmaker()
    submission = insert_submission(session.get_bind())
    autograde_task.request.id = "test-task-id"
    autograde_task._sessions = {"test-task-id": session}

    with pytest.raises(ValueError, match="invalid submission"):
        autograde_task.run(
            lecture_id=999,  # Wrong lecture ID
            assignment_id=submission.assignid,
            sub_id=submission.id,
        )

    autograde_task._sessions["test-task-id"].close()


def test_celery_generate_feedback_task_success(sql_alchemy_sessionmaker, celery_app):
    """Test that generate_feedback_task runs without errors with valid inputs."""
    session = sql_alchemy_sessionmaker()
    submission = insert_submission(session.get_bind())
    generate_feedback_task.request.id = "test-task-id"
    generate_feedback_task._sessions = {"test-task-id": session}

    def mock_start():
        sub = session.get(Submission, submission.id)
        sub.feedback_status = FeedbackStatus.GENERATED
        session.commit()

    with (
        patch.object(LocalFeedbackExecutor, "start", side_effect=mock_start) as feedback_mock,
        patch.object(autograde_task.log, "info", return_value=MagicMock()),
    ):
        generate_feedback_task.run(
            lecture_id=submission.assignment.lectid,
            assignment_id=submission.assignid,
            sub_id=submission.id,
        )

        feedback_mock.assert_called_once()
        sub = session.get(Submission, submission.id)
        assert sub.feedback_status == FeedbackStatus.GENERATED
        generate_feedback_task.log.info.assert_called_once()

    generate_feedback_task._sessions["test-task-id"].close()


def test_celery_generate_feedback_task_invalid_submission_id(sql_alchemy_sessionmaker, celery_app):
    """Test that generate_feedback_task raises error for non-existent submission."""
    session = sql_alchemy_sessionmaker()
    generate_feedback_task.request.id = "test-task-id"
    generate_feedback_task._sessions = {"test-task-id": session}

    with pytest.raises(ValueError, match="Submission not found"):
        generate_feedback_task.run(
            lecture_id=1,
            assignment_id=1,
            sub_id=99999,  # Non-existent submission
        )

    generate_feedback_task._sessions["test-task-id"].close()


def test_celery_generate_feedback_task_mismatched_ids(sql_alchemy_sessionmaker, celery_app):
    """Test that generate_feedback_task raises error when IDs of lecture and submission don't match."""
    session = sql_alchemy_sessionmaker()
    submission = insert_submission(session.get_bind())
    generate_feedback_task.request.id = "test-task-id"
    generate_feedback_task._sessions = {"test-task-id": session}

    with pytest.raises(ValueError, match="invalid submission"):
        generate_feedback_task.run(
            lecture_id=999,  # Wrong lecture ID
            assignment_id=submission.assignid,
            sub_id=submission.id,
        )

    generate_feedback_task._sessions["test-task-id"].close()


def test_celery_lti_sync_task_success(sql_alchemy_sessionmaker, celery_app):
    """Test successful LTI grade sync"""
    lti_sync_task.request.id = "test-task-id"
    session = sql_alchemy_sessionmaker()
    lti_sync_task._sessions = {"test-task-id": session}

    result = lti_sync_task.run(
        lecture={"id": 1}, assignment={"id": 1}, submissions=[{"id": 1}], feedback_sync=False
    )

    assert result == _lti_sync_result
    mock_plugin = lti_sync_task.celery.plugin_manager.get("lti")
    mock_plugin.start.assert_called_once()

    lti_sync_task._sessions["test-task-id"].close()
