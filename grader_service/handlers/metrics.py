# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import os
from datetime import UTC, datetime, timedelta
from http import HTTPStatus

from sqlalchemy import func
from tornado.web import HTTPError

from grader_service.handlers.base_handler import GraderBaseHandler
from grader_service.orm.assignment import Assignment
from grader_service.orm.base import DeleteState
from grader_service.orm.lecture import Lecture, LectureState
from grader_service.orm.submission import AutoStatus, FeedbackStatus, ManualStatus, Submission
from grader_service.orm.takepart import Role, Scope
from grader_service.orm.user import User
from grader_service.registry import VersionSpecifier, register_handler


def _get_dir_size(path: str) -> int:
    """Recursively compute total size in bytes of a directory tree."""
    total = 0
    try:
        for dirpath, _dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    total += os.path.getsize(fp)
                except OSError:
                    pass
    except OSError:
        pass
    return total


def _format_gauge(name: str, help_text: str, value, labels: dict | None = None) -> str:
    """Format a single Prometheus gauge metric line."""
    lines = []
    lines.append(f"# HELP {name} {help_text}")
    lines.append(f"# TYPE {name} gauge")
    if labels:
        label_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
        lines.append(f"{name}{{{label_str}}} {value}")
    else:
        lines.append(f"{name} {value}")
    return "\n".join(lines)


def _format_gauge_family(name: str, help_text: str, entries: list[tuple[dict, float]]) -> str:
    """Format a Prometheus gauge metric family with multiple label sets."""
    lines = []
    lines.append(f"# HELP {name} {help_text}")
    lines.append(f"# TYPE {name} gauge")
    for labels, value in entries:
        label_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
        lines.append(f"{name}{{{label_str}}} {value}")
    return "\n".join(lines)


@register_handler(path=r"\/api\/metrics\/?", version_specifier=VersionSpecifier.ALL)
class MetricsHandler(GraderBaseHandler):
    """
    Tornado Handler class for http requests to /api/metrics.
    Returns Prometheus-compatible metrics in text exposition format.
    """

    async def get(self):
        try:
            metrics = self._collect_metrics()
        except Exception as e:
            self.log.error(f"Error collecting metrics: {e}")
            raise HTTPError(HTTPStatus.INTERNAL_SERVER_ERROR, reason="Error collecting metrics")

        self.set_header("Content-Type", "text/plain")
        self.write(metrics)

    def _collect_metrics(self) -> str:
        sections = []

        # Lecture metrics
        sections.append(self._lecture_metrics())

        # Assignment metrics
        sections.append(self._assignment_metrics())

        # User metrics
        sections.append(self._user_metrics())

        # Role metrics
        sections.append(self._role_metrics())

        # Submission metrics
        sections.append(self._submission_metrics())

        # Submission status breakdown
        sections.append(self._submission_status_metrics())

        # Submissions by date (last 90 days)
        sections.append(self._submissions_by_date_metrics())

        # Git storage metrics
        sections.append(self._git_storage_metrics())

        return "\n\n".join(sections) + "\n"

    def _lecture_metrics(self) -> str:
        entries = []
        for state in LectureState:
            count = (
                self.session.query(func.count(Lecture.id))
                .filter(Lecture.state == state, Lecture.deleted == DeleteState.active)
                .scalar()
            )
            entries.append(({"state": state.name}, float(count)))

        result = _format_gauge_family(
            "grader_lectures_total", "Total number of lectures by state.", entries
        )
        return result

    def _assignment_metrics(self) -> str:
        entries = []
        for status in ("created", "pushed", "released", "complete"):
            count = (
                self.session.query(func.count(Assignment.id))
                .filter(Assignment.status == status, Assignment.deleted == DeleteState.active)
                .scalar()
            )
            entries.append(({"status": status}, float(count)))

        return _format_gauge_family(
            "grader_assignments_total", "Total number of assignments by status.", entries
        )

    def _user_metrics(self) -> str:
        count = self.session.query(func.count(User.id)).scalar()
        return _format_gauge("grader_users_total", "Total number of registered users.", count)

    def _role_metrics(self) -> str:
        entries = []
        for scope in Scope:
            count = (
                self.session.query(func.count())
                .select_from(Role)
                .filter(Role.role == scope)
                .scalar()
            )
            entries.append(({"scope": scope.name}, float(count)))

        return _format_gauge_family(
            "grader_roles_total", "Total number of role assignments by scope.", entries
        )

    def _submission_metrics(self) -> str:
        count = (
            self.session.query(func.count(Submission.id))
            .filter(Submission.deleted == DeleteState.active)
            .scalar()
        )
        return _format_gauge("grader_submissions_total", "Total number of submissions.", count)

    def _submission_status_metrics(self) -> str:
        sections = []

        # Autograding status
        auto_entries = []
        for status in AutoStatus:
            count = (
                self.session.query(func.count(Submission.id))
                .filter(Submission.auto_status == status, Submission.deleted == DeleteState.active)
                .scalar()
            )
            auto_entries.append(({"status": status.value}, float(count)))
        sections.append(
            _format_gauge_family(
                "grader_submissions_autograding_status",
                "Number of submissions by autograding status.",
                auto_entries,
            )
        )

        # Manual grading status
        manual_entries = []
        for status in ManualStatus:
            count = (
                self.session.query(func.count(Submission.id))
                .filter(
                    Submission.manual_status == status, Submission.deleted == DeleteState.active
                )
                .scalar()
            )
            manual_entries.append(({"status": status.value}, float(count)))
        sections.append(
            _format_gauge_family(
                "grader_submissions_manual_status",
                "Number of submissions by manual grading status.",
                manual_entries,
            )
        )

        # Feedback status
        feedback_entries = []
        for status in FeedbackStatus:
            count = (
                self.session.query(func.count(Submission.id))
                .filter(
                    Submission.feedback_status == status, Submission.deleted == DeleteState.active
                )
                .scalar()
            )
            feedback_entries.append(({"status": status.value}, float(count)))
        sections.append(
            _format_gauge_family(
                "grader_submissions_feedback_status",
                "Number of submissions by feedback generation status.",
                feedback_entries,
            )
        )

        return "\n\n".join(sections)

    def _submissions_by_date_metrics(self) -> str:
        cutoff = datetime.now(UTC) - timedelta(days=90)
        # Use func.date() for cross-DB compatibility (works with both PostgreSQL and SQLite)
        date_col = func.date(Submission.date)
        rows = (
            self.session.query(date_col.label("day"), func.count(Submission.id).label("count"))
            .filter(Submission.date >= cutoff, Submission.deleted == DeleteState.active)
            .group_by(date_col)
            .order_by(date_col)
            .all()
        )

        entries = []
        for day, count in rows:
            entries.append(({"date": str(day)}, float(count)))

        if not entries:
            return (
                "# HELP grader_submissions_by_date Number of submissions per date (last 90 days).\n"
                "# TYPE grader_submissions_by_date gauge"
            )

        return _format_gauge_family(
            "grader_submissions_by_date", "Number of submissions per date (last 90 days).", entries
        )

    def _git_storage_metrics(self) -> str:
        git_dir = os.path.join(self.application.grader_service_dir, "git")
        total_bytes = _get_dir_size(git_dir)

        return _format_gauge(
            "grader_git_storage_bytes",
            "Total size of all git repositories on disk in bytes.",
            total_bytes,
        )
