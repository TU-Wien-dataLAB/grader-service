# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import os
import re
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from grader_service.orm.base import DeleteState
from grader_service.orm.submission import AutoStatus, FeedbackStatus, ManualStatus, Submission
from grader_service.server import GraderServer


def _parse_metric(body: str, metric_name: str) -> list[tuple[dict, float]]:
    """Parse all metric lines for a given metric name from Prometheus text output.

    Returns a list of (labels_dict, value) tuples.
    """
    results = []
    pattern = re.compile(rf"^{re.escape(metric_name)}(?:\{{([^}}]*)\}})?\s+(.+)$", re.MULTILINE)
    for match in pattern.finditer(body):
        labels_str, value_str = match.group(1), match.group(2)
        labels = {}
        if labels_str:
            for pair in labels_str.split(","):
                k, v = pair.split("=", 1)
                labels[k.strip()] = v.strip().strip('"')
        results.append((labels, float(value_str)))
    return results


def _get_metric_value(body: str, metric_name: str, labels: dict | None = None) -> float | None:
    """Get the value of a specific metric with optional label matching."""
    parsed = _parse_metric(body, metric_name)
    for metric_labels, value in parsed:
        if labels is None and not metric_labels:
            return value
        if labels is not None and all(metric_labels.get(k) == v for k, v in labels.items()):
            return value
    return None


def _insert_submission_with_status(
    engine: Engine,
    assignment_id: int = 1,
    user_id: int = 1,
    auto_status: AutoStatus = AutoStatus.NOT_GRADED,
    manual_status: ManualStatus = ManualStatus.NOT_GRADED,
    feedback_status: FeedbackStatus = FeedbackStatus.NOT_GENERATED,
    score: float | None = None,
    date: datetime | None = None,
) -> Submission:
    """Insert a submission with specific status fields for testing."""
    session: Session = sessionmaker(engine)()
    s = Submission()
    s.date = date or datetime.now(tz=timezone.utc)
    s.auto_status = auto_status
    s.manual_status = manual_status
    s.assignid = assignment_id
    s.user_id = user_id
    s.score = score
    s.commit_hash = secrets.token_hex(20)
    s.feedback_status = feedback_status
    s.deleted = DeleteState.active
    s.edited = False
    s.grading_score = score or 0.0
    session.add(s)
    session.commit()
    session.refresh(s)
    session.flush()
    return s


# ---------------------------------------------------------------------------
# Test: Basic endpoint reachability (no auth required)
# ---------------------------------------------------------------------------


async def test_metrics_returns_200(app: GraderServer, service_base_url, http_server_client):
    """The /api/metrics endpoint should be reachable without authentication."""
    url = service_base_url + "metrics"
    response = await http_server_client.fetch(url)
    assert response.code == 200


async def test_metrics_content_type(app: GraderServer, service_base_url, http_server_client):
    """Response Content-Type must be Prometheus text exposition format."""
    url = service_base_url + "metrics"
    response = await http_server_client.fetch(url)
    content_type = response.headers.get("Content-Type", "")
    assert "text/plain" in content_type


async def test_metrics_no_auth_required(app: GraderServer, service_base_url, http_server_client):
    """The endpoint must work without an Authorization header."""
    url = service_base_url + "metrics"
    # Explicitly do NOT pass any auth headers
    response = await http_server_client.fetch(url, headers={})
    assert response.code == 200


# ---------------------------------------------------------------------------
# Test: Prometheus format compliance
# ---------------------------------------------------------------------------


async def test_metrics_prometheus_format(app: GraderServer, service_base_url, http_server_client):
    """All metrics must have # HELP and # TYPE lines."""
    url = service_base_url + "metrics"
    response = await http_server_client.fetch(url)
    body = response.body.decode()

    expected_metrics = [
        "grader_lectures_total",
        "grader_assignments_total",
        "grader_users_total",
        "grader_roles_total",
        "grader_submissions_total",
        "grader_submissions_autograding_status",
        "grader_submissions_manual_status",
        "grader_submissions_feedback_status",
        "grader_submissions_by_date",
        "grader_git_storage_bytes",
    ]

    for metric in expected_metrics:
        assert f"# HELP {metric} " in body, f"Missing HELP for {metric}"
        assert f"# TYPE {metric} gauge" in body, f"Missing TYPE for {metric}"


# ---------------------------------------------------------------------------
# Test: Lecture metrics
# ---------------------------------------------------------------------------


async def test_metrics_lecture_counts(app: GraderServer, service_base_url, http_server_client):
    """Verifies lecture counts match seeded data (4 active lectures)."""
    url = service_base_url + "metrics"
    response = await http_server_client.fetch(url)
    body = response.body.decode()

    # The default fixture inserts 4 active lectures
    active_count = _get_metric_value(body, "grader_lectures_total", {"state": "active"})
    assert active_count == 4.0

    complete_count = _get_metric_value(body, "grader_lectures_total", {"state": "complete"})
    assert complete_count == 0.0


# ---------------------------------------------------------------------------
# Test: Assignment metrics
# ---------------------------------------------------------------------------


async def test_metrics_assignment_counts(app: GraderServer, service_base_url, http_server_client):
    """Verifies assignment counts match seeded data (1 released, 1 created)."""
    url = service_base_url + "metrics"
    response = await http_server_client.fetch(url)
    body = response.body.decode()

    released = _get_metric_value(body, "grader_assignments_total", {"status": "released"})
    assert released == 1.0

    created = _get_metric_value(body, "grader_assignments_total", {"status": "created"})
    assert created == 1.0

    pushed = _get_metric_value(body, "grader_assignments_total", {"status": "pushed"})
    assert pushed == 0.0

    complete = _get_metric_value(body, "grader_assignments_total", {"status": "complete"})
    assert complete == 0.0


# ---------------------------------------------------------------------------
# Test: User metrics
# ---------------------------------------------------------------------------


async def test_metrics_user_count(app: GraderServer, service_base_url, http_server_client):
    """Default fixture inserts 1 user ('ubuntu')."""
    url = service_base_url + "metrics"
    response = await http_server_client.fetch(url)
    body = response.body.decode()

    user_count = _get_metric_value(body, "grader_users_total")
    assert user_count == 1


# ---------------------------------------------------------------------------
# Test: Role metrics
# ---------------------------------------------------------------------------


async def test_metrics_role_counts(
    app: GraderServer, service_base_url, http_server_client, sql_alchemy_engine, default_roles
):
    """After default_roles seeding, verifies role counts by scope."""
    url = service_base_url + "metrics"
    response = await http_server_client.fetch(url)
    body = response.body.decode()

    # default_roles assigns: ubuntu=instructor in 20wle2 & 22wle1, ubuntu=student in 21wle1,
    # debian=instructor in 23wle1
    student_count = _get_metric_value(body, "grader_roles_total", {"scope": "student"})
    assert student_count == 1.0

    instructor_count = _get_metric_value(body, "grader_roles_total", {"scope": "instructor"})
    assert instructor_count == 3.0  # ubuntu x2 + debian x1


# ---------------------------------------------------------------------------
# Test: Submission metrics with data
# ---------------------------------------------------------------------------


async def test_metrics_autograding_status_breakdown(
    app: GraderServer, service_base_url, http_server_client, sql_alchemy_engine
):
    """Verify the autograding status gauge family."""
    engine = sql_alchemy_engine

    _insert_submission_with_status(engine, auto_status=AutoStatus.AUTOMATICALLY_GRADED, score=10.0)
    _insert_submission_with_status(engine, auto_status=AutoStatus.GRADING_FAILED)
    _insert_submission_with_status(engine, auto_status=AutoStatus.GRADING_FAILED)

    url = service_base_url + "metrics"
    response = await http_server_client.fetch(url)
    body = response.body.decode()

    auto_graded = _get_metric_value(
        body, "grader_submissions_autograding_status", {"status": "automatically_graded"}
    )
    assert auto_graded == 1.0

    grading_failed = _get_metric_value(
        body, "grader_submissions_autograding_status", {"status": "grading_failed"}
    )
    assert grading_failed == 2.0

    not_graded = _get_metric_value(
        body, "grader_submissions_autograding_status", {"status": "not_graded"}
    )
    assert not_graded == 0.0


async def test_metrics_manual_status_breakdown(
    app: GraderServer, service_base_url, http_server_client, sql_alchemy_engine
):
    """Verify the manual grading status gauge family."""
    engine = sql_alchemy_engine

    _insert_submission_with_status(engine, manual_status=ManualStatus.MANUALLY_GRADED, score=10.0)
    _insert_submission_with_status(engine, manual_status=ManualStatus.NOT_GRADED)

    url = service_base_url + "metrics"
    response = await http_server_client.fetch(url)
    body = response.body.decode()

    manually_graded = _get_metric_value(
        body, "grader_submissions_manual_status", {"status": "manually_graded"}
    )
    assert manually_graded == 1.0

    not_graded = _get_metric_value(
        body, "grader_submissions_manual_status", {"status": "not_graded"}
    )
    assert not_graded == 1.0


async def test_metrics_feedback_status_breakdown(
    app: GraderServer, service_base_url, http_server_client, sql_alchemy_engine
):
    """Verify the feedback status gauge family."""
    engine = sql_alchemy_engine

    _insert_submission_with_status(engine, feedback_status=FeedbackStatus.GENERATED)
    _insert_submission_with_status(engine, feedback_status=FeedbackStatus.GENERATION_FAILED)
    _insert_submission_with_status(engine, feedback_status=FeedbackStatus.NOT_GENERATED)

    url = service_base_url + "metrics"
    response = await http_server_client.fetch(url)
    body = response.body.decode()

    generated = _get_metric_value(
        body, "grader_submissions_feedback_status", {"status": "generated"}
    )
    assert generated == 1.0

    gen_failed = _get_metric_value(
        body, "grader_submissions_feedback_status", {"status": "generation_failed"}
    )
    assert gen_failed == 1.0


# ---------------------------------------------------------------------------
# Test: Submissions by date
# ---------------------------------------------------------------------------


async def test_metrics_submissions_by_date(
    app: GraderServer, service_base_url, http_server_client, sql_alchemy_engine
):
    """Submissions on different dates should appear as separate date labels."""
    engine = sql_alchemy_engine

    today = datetime.now(tz=timezone.utc)
    yesterday = today - timedelta(days=1)
    two_days_ago = today - timedelta(days=2)

    _insert_submission_with_status(engine, date=today)
    _insert_submission_with_status(engine, date=today)
    _insert_submission_with_status(engine, date=yesterday)
    _insert_submission_with_status(engine, date=two_days_ago)

    url = service_base_url + "metrics"
    response = await http_server_client.fetch(url)
    body = response.body.decode()

    today_count = _get_metric_value(body, "grader_submissions_by_date", {"date": str(today.date())})
    assert today_count == 2.0

    yesterday_count = _get_metric_value(
        body, "grader_submissions_by_date", {"date": str(yesterday.date())}
    )
    assert yesterday_count == 1.0


async def test_metrics_submissions_by_date_excludes_old(
    app: GraderServer, service_base_url, http_server_client, sql_alchemy_engine
):
    """Submissions older than 90 days should not appear in by_date metrics."""
    engine = sql_alchemy_engine

    old_date = datetime.now(tz=timezone.utc) - timedelta(days=100)
    _insert_submission_with_status(engine, date=old_date)

    url = service_base_url + "metrics"
    response = await http_server_client.fetch(url)
    body = response.body.decode()

    old_count = _get_metric_value(
        body, "grader_submissions_by_date", {"date": str(old_date.date())}
    )
    assert old_count is None  # Should not appear

    # But the submission still counts in total
    total = _get_metric_value(body, "grader_submissions_total")
    assert total == 1


# ---------------------------------------------------------------------------
# Test: Git storage metrics
# ---------------------------------------------------------------------------


async def test_metrics_git_storage_empty(app: GraderServer, service_base_url, http_server_client):
    """With no git repos, storage should be 0."""
    url = service_base_url + "metrics"
    response = await http_server_client.fetch(url)
    body = response.body.decode()

    storage = _get_metric_value(body, "grader_git_storage_bytes")
    assert storage == 0


async def test_metrics_git_storage_with_files(
    app: GraderServer, service_base_url, http_server_client
):
    """Creating files in the git directory should be reflected in storage metrics."""
    # Create a git directory with some test files
    git_dir = os.path.join(app.grader_service_dir, "git")
    os.makedirs(git_dir, exist_ok=True)

    test_file = os.path.join(git_dir, "test_repo", "test_file.txt")
    os.makedirs(os.path.dirname(test_file), exist_ok=True)
    with open(test_file, "w") as f:
        f.write("x" * 1024)  # 1KB file

    url = service_base_url + "metrics"
    response = await http_server_client.fetch(url)
    body = response.body.decode()

    storage = _get_metric_value(body, "grader_git_storage_bytes")
    assert storage >= 1024


# ---------------------------------------------------------------------------
# Test: Versioned endpoint
# ---------------------------------------------------------------------------


async def test_metrics_versioned_endpoint(app: GraderServer, service_base_url, http_server_client):
    """The /v1/api/metrics endpoint should also work (VersionSpecifier.ALL)."""
    url = "/v1/api/metrics"
    response = await http_server_client.fetch(url)
    assert response.code == 200
    body = response.body.decode()
    assert "grader_lectures_total" in body


# ---------------------------------------------------------------------------
# Test: Deleted entities are excluded
# ---------------------------------------------------------------------------


async def test_metrics_excludes_deleted_submissions(
    app: GraderServer, service_base_url, http_server_client, sql_alchemy_engine
):
    """Deleted submissions should not be counted in metrics."""
    engine = sql_alchemy_engine

    # Insert an active submission
    _insert_submission_with_status(engine, auto_status=AutoStatus.AUTOMATICALLY_GRADED, score=10.0)

    # Insert a deleted submission
    session: Session = sessionmaker(engine)()
    s = Submission()
    s.date = datetime.now(tz=timezone.utc)
    s.auto_status = AutoStatus.AUTOMATICALLY_GRADED
    s.manual_status = ManualStatus.NOT_GRADED
    s.assignid = 1
    s.user_id = 1
    s.score = 20.0
    s.commit_hash = secrets.token_hex(20)
    s.feedback_status = FeedbackStatus.NOT_GENERATED
    s.deleted = DeleteState.deleted
    s.edited = False
    s.grading_score = 20.0
    session.add(s)
    session.commit()

    url = service_base_url + "metrics"
    response = await http_server_client.fetch(url)
    body = response.body.decode()

    # Only the active submission should be counted
    total = _get_metric_value(body, "grader_submissions_total")
    assert total == 1.0

    auto_graded = _get_metric_value(
        body, "grader_submissions_autograding_status", {"status": "automatically_graded"}
    )
    assert auto_graded == 1.0
