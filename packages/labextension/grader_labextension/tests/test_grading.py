import os

import pytest

from grader_labextension.handlers.grading import _sanitize_filename


def test_sanitize_filename_without_separators():
    """Names without path separators are returned unchanged."""
    assert _sanitize_filename("Example Assignment") == "Example Assignment"


@pytest.mark.parametrize(
    "name, expected",
    [
        ("Example / Assignment", "Example _ Assignment"),
        ("/leading/slash", "_leading_slash"),
        ("trailing/slash/", "trailing_slash_"),
        ("multiple///slash", "multiple___slash"),
    ],
)
def test_sanitize_filename_replaces_forward_slash(name, expected, monkeypatch):
    """Forward path separators in an assignment name are replaced with underscores."""
    # Force POSIX separators so the expectation is deterministic across
    # platforms.
    monkeypatch.setattr(os, "sep", "/")
    monkeypatch.setattr(os, "altsep", None)

    assert _sanitize_filename(name) == expected


def test_sanitize_filename_replaces_altsep(monkeypatch):
    """When os.altsep is set (e.g. ``/`` on Windows) it is also replaced."""
    monkeypatch.setattr(os, "sep", "\\")
    monkeypatch.setattr(os, "altsep", "/")

    assert _sanitize_filename("Example / Assignment") == "Example _ Assignment"


def test_sanitize_filename_produces_single_path_component(tmp_path, monkeypatch):
    """The sanitized name must not introduce additional path components."""
    monkeypatch.setattr(os, "sep", "/")
    monkeypatch.setattr(os, "altsep", None)

    sanitized = _sanitize_filename("Example / Assignment")
    # Writing a file with the sanitized name in a directory must succeed and
    # must create exactly one file rather than nested directories.
    file_path = tmp_path / f"{sanitized}_none_submissions.csv"
    file_path.write_text("content")

    assert file_path.is_file()
    assert len(list(tmp_path.iterdir())) == 1
