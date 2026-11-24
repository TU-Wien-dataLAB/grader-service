# Copyright (c) 2022, TU Wien
# All rights reserved.
#
import logging
import shutil
import subprocess
from pathlib import Path

import pytest
from traitlets.config import Config

from grader_labextension.api.models.remote_file_status import RemoteFileStatus
from grader_labextension.services.git import GitError, GitService
from grader_service.artifact_types import ArtifactType

# A logger that suppresses output from the (chatty) command runner during tests.
_TEST_LOG = logging.getLogger("test_gitservice")
_TEST_LOG.addHandler(logging.NullHandler())
_TEST_LOG.propagate = False


def run_git(*args, cwd=None):
    """Run a real git command and return its stdout."""
    result = subprocess.run(["git", *args], cwd=cwd, check=True, text=True, capture_output=True)
    return result.stdout


def make_git_service(
    tmp_path, lecture_code="21wle1", assignment_id=1, artifact_type=ArtifactType.USER, **kwargs
) -> GitService:
    """Create a GitService bound to a temporary server root directory."""
    config = Config(
        {
            "GitService": {
                "git_access_token": "test-token",
                "git_service_url": "http://example.com/services/grader/git",
            }
        }
    )
    return GitService(
        server_root_dir=str(tmp_path),
        lecture_code=lecture_code,
        assignment_id=assignment_id,
        artifact_type=artifact_type,
        config=config,
        log=_TEST_LOG,
        **kwargs,
    )


@pytest.fixture
def git_service(tmp_path):
    """A GitService with an empty (pre-created) working directory."""
    return make_git_service(tmp_path)


def init_service_with_commit(service: GitService, message="initial commit", files=None):
    """Initialize the service's repo, commit optional files, and return the hash."""
    service.init()
    service.set_author("Test Author")
    files = files or []
    for name, content in files:
        path = service.path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    service.commit(message)
    return run_git("rev-parse", "HEAD", cwd=service.path).strip()


def create_populated_remote(tmp_path, name="assignment.ipynb") -> Path:
    """Create a bare remote repository with a ``main`` branch and one file."""
    remote_dir = tmp_path / "remote"
    remote_dir.mkdir(exist_ok=True)
    remote_path = remote_dir / "bare.git"
    run_git("init", "--bare", "-b", "main", str(remote_path), cwd=tmp_path)

    work = tmp_path / "clone"
    work.mkdir()
    run_git("clone", str(remote_path), str(work), cwd=tmp_path)
    run_git("config", "user.name", "Tester", cwd=work)
    run_git("config", "user.email", "tester@example.com", cwd=work)
    (work / name).write_text("# contents")
    run_git("add", name, cwd=work)
    run_git("commit", "-m", "initial", cwd=work)
    run_git("push", "-u", "origin", "main", cwd=work)
    return remote_path


def attach_remote(service: GitService, remote_path: Path):
    service.init()
    run_git("remote", "add", "origin", str(remote_path), cwd=service.path)
    run_git("fetch", "origin", cwd=service.path)
    run_git("checkout", "-B", "main", "--track", "origin/main", cwd=service.path)


# ---------------------------------------------------------------------------
# GitError
# ---------------------------------------------------------------------------


def test_git_error_holds_code_and_message():
    error = GitError(code=404, error="nope")
    assert error.code == 404
    assert error.error == "nope"
    assert str(error) == "nope"


def test_git_error_defaults():
    error = GitError()
    assert error.code == 500
    assert error.error == "Unknown Error"


# ---------------------------------------------------------------------------
# Repository path determination
# ---------------------------------------------------------------------------


def test_path_for_user_artifact_uses_assignments_dir(tmp_path):
    service = make_git_service(tmp_path, artifact_type=ArtifactType.USER)
    assert service.path == tmp_path / "21wle1" / "assignments" / "1"


def test_path_for_user_artifact_forced_uses_assignments_dir(tmp_path):
    service = make_git_service(tmp_path, artifact_type=ArtifactType.USER, force_user_artifact=True)
    assert service.path == tmp_path / "21wle1" / "assignments" / "1"


@pytest.mark.parametrize(
    "artifact_type, expected_subdir",
    [
        (ArtifactType.SOURCE, "source"),
        (ArtifactType.RELEASE, "release"),
        (ArtifactType.AUTOGRADE, "autograde"),
        (ArtifactType.FEEDBACK, "feedback"),
    ],
)
def test_path_for_simple_artifact_types(tmp_path, artifact_type, expected_subdir):
    service = make_git_service(tmp_path, artifact_type=artifact_type)
    assert service.path == tmp_path / "21wle1" / expected_subdir / "1"


def test_path_for_edit_artifact_with_username(tmp_path):
    service = make_git_service(tmp_path, artifact_type=ArtifactType.EDIT, username="alice")
    assert service.path == tmp_path / "21wle1" / "create" / "1" / "alice"


def test_path_for_edit_artifact_with_submission_id(tmp_path):
    service = make_git_service(tmp_path, artifact_type=ArtifactType.EDIT, sub_id=42)
    assert service.path == tmp_path / "21wle1" / "edit" / "1" / "42"


def test_path_includes_lecture_code(tmp_path):
    service = make_git_service(tmp_path, lecture_code="22wle2", artifact_type=ArtifactType.SOURCE)
    assert service.path == tmp_path / "22wle2" / "source" / "1"


def test_repo_dir_is_created_on_service_creation(git_service):
    assert git_service.path.is_dir()


# ---------------------------------------------------------------------------
# is_git
# ---------------------------------------------------------------------------


def test_is_git_false_for_fresh_directory(git_service):
    assert git_service.is_git() is False


def test_is_git_true_after_init(git_service):
    git_service.init()
    assert git_service.is_git() is True
    assert (git_service.path / ".git").exists()


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------


def test_init_creates_git_repository(git_service):
    git_service.init()
    assert git_service.is_git()
    assert run_git("branch", "--show-current", cwd=git_service.path).strip() == "main"


def test_init_is_idempotent(git_service):
    git_service.init()
    git_service.init()
    assert git_service.is_git()


def test_init_forces_reinitialization(git_service):
    git_service.init()
    shutil.rmtree(git_service.path / ".git")
    assert not git_service.is_git()
    git_service.init(force=True)
    assert git_service.is_git()


# ---------------------------------------------------------------------------
# set_author
# ---------------------------------------------------------------------------


def test_set_author_configures_user(git_service):
    git_service.init()
    git_service.set_author("Jane Doe")
    assert run_git("config", "user.name", cwd=git_service.path).strip() == "Jane Doe"
    assert run_git("config", "user.email", cwd=git_service.path).strip() == "sample@mail.com"


# ---------------------------------------------------------------------------
# commit
# ---------------------------------------------------------------------------


def test_commit_adds_all_files(git_service):
    git_service.init()
    git_service.set_author("Test Author")
    (git_service.path / "a.txt").write_text("a")
    (git_service.path / "b.txt").write_text("b")
    git_service.commit("add everything")
    log = run_git("log", "--pretty=%s", cwd=git_service.path)
    assert "add everything" in log


def test_commit_selected_files_only(git_service):
    git_service.init()
    git_service.set_author("Test Author")
    (git_service.path / "keep.txt").write_text("keep")
    (git_service.path / "skip.txt").write_text("skip")
    git_service.commit("selected", selected_files=["keep.txt"])
    tracked = run_git("ls-files", cwd=git_service.path)
    assert "keep.txt" in tracked
    assert "skip.txt" not in tracked


def test_commit_allows_empty_commit(git_service):
    git_service.init()
    git_service.set_author("Test Author")
    git_service.commit("empty")
    assert run_git("log", "--pretty=%s", cwd=git_service.path).strip() == "empty"


# ---------------------------------------------------------------------------
# git_status
# ---------------------------------------------------------------------------


def test_git_status_detects_untracked(git_service):
    git_service.init()
    (git_service.path / "new.txt").write_text("x")
    untracked, added, modified, deleted = git_service.git_status()
    assert "new.txt" in untracked


def test_git_status_detects_modified(git_service):
    service = git_service
    init_service_with_commit(service, files=[("file.txt", "v1")])
    (service.path / "file.txt").write_text("v2")
    untracked, added, modified, deleted = service.git_status()
    assert modified == ["file.txt"]


def test_git_status_detects_deleted(git_service):
    service = git_service
    init_service_with_commit(service, files=[("file.txt", "v1")])
    (service.path / "file.txt").unlink()
    untracked, added, modified, deleted = service.git_status()
    assert deleted == ["file.txt"]


def test_git_status_detects_added_when_staged(git_service):
    service = git_service
    init_service_with_commit(service)
    (service.path / "staged.txt").write_text("x")
    run_git("add", "staged.txt", cwd=service.path)
    untracked, added, modified, deleted = service.git_status()
    assert added == ["staged.txt"]


def test_git_status_hides_hidden_files_by_default(git_service):
    git_service.init()
    (git_service.path / ".hidden").write_text("h")
    untracked, *_ = git_service.git_status()
    assert ".hidden" not in untracked
    untracked, *_ = git_service.git_status(hidden_files=True)
    assert ".hidden" in untracked


def test_git_status_parses_all_porcelain_states(monkeypatch, git_service):
    output = "\n".join(["?? untracked.txt", "A  added.txt", "M  modified.txt", "D  deleted.txt"])
    monkeypatch.setattr(git_service, "_run_command", lambda command, cwd: output)
    assert git_service.git_status() == (
        ["untracked.txt"],
        ["added.txt"],
        ["modified.txt"],
        ["deleted.txt"],
    )


# ---------------------------------------------------------------------------
# check_remote_file_status
# ---------------------------------------------------------------------------


def test_check_remote_file_status_clean_returns_up_to_date(monkeypatch, git_service):
    monkeypatch.setattr(git_service, "_run_command", lambda command, cwd: "")
    assert git_service.check_remote_file_status("file.txt") == RemoteFileStatus.UP_TO_DATE


@pytest.mark.parametrize("status_char", ["??", "M", "A", "D"])
def test_check_remote_file_status_unsaved_for_changes(monkeypatch, git_service, status_char):
    monkeypatch.setattr(git_service, "_run_command", lambda command, cwd: f"{status_char} file.txt")
    assert git_service.check_remote_file_status("file.txt") == RemoteFileStatus.UNSAVED_CHANGES


def test_check_remote_file_status_divergent_for_renames(monkeypatch, git_service):
    monkeypatch.setattr(git_service, "_run_command", lambda command, cwd: "R  old.txt new.txt")
    assert git_service.check_remote_file_status("new.txt") == RemoteFileStatus.DIVERGENT


# ---------------------------------------------------------------------------
# check_remote_status
# ---------------------------------------------------------------------------


def test_check_remote_status_up_to_date(tmp_path):
    remote = create_populated_remote(tmp_path)
    service = make_git_service(tmp_path / "svc")
    attach_remote(service, remote)
    assert service.check_remote_status("origin", "main") == RemoteFileStatus.UP_TO_DATE


def test_check_remote_status_unsaved_changes(tmp_path):
    remote = create_populated_remote(tmp_path)
    service = make_git_service(tmp_path / "svc")
    attach_remote(service, remote)
    (service.path / "local.txt").write_text("mine")
    assert service.check_remote_status("origin", "main") == RemoteFileStatus.UNSAVED_CHANGES


def test_check_remote_status_update_needed_when_remote_ahead(tmp_path):
    remote = create_populated_remote(tmp_path)
    service = make_git_service(tmp_path / "svc")
    attach_remote(service, remote)

    # Advance the remote with an extra commit.
    work = tmp_path / "clone"
    (work / "assignment.ipynb").write_text("# updated")
    run_git("add", "assignment.ipynb", cwd=work)
    run_git("commit", "-m", "remote update", cwd=work)
    run_git("push", "origin", "main", cwd=work)
    run_git("fetch", "origin", cwd=service.path)

    assert service.check_remote_status("origin", "main") == RemoteFileStatus.UPDATE_NEEDED


def test_check_remote_status_divergent(tmp_path):
    remote = create_populated_remote(tmp_path)
    service = make_git_service(tmp_path / "svc")
    attach_remote(service, remote)

    # Local commit ...
    (service.path / "local.txt").write_text("mine")
    run_git("add", "local.txt", cwd=service.path)
    run_git("commit", "-m", "local", cwd=service.path)
    # ... and a remote commit, so the histories diverge.
    work = tmp_path / "clone"
    (work / "assignment.ipynb").write_text("# diverged")
    run_git("add", "assignment.ipynb", cwd=work)
    run_git("commit", "-m", "remote", cwd=work)
    run_git("push", "origin", "main", cwd=work)
    run_git("fetch", "origin", cwd=service.path)

    assert service.check_remote_status("origin", "main") == RemoteFileStatus.DIVERGENT


def test_check_remote_status_no_backup_when_remote_branch_missing(monkeypatch, git_service):
    git_service.init()
    monkeypatch.setattr(git_service, "remote_branch_exists", lambda origin, branch: False)
    assert git_service.check_remote_status("origin", "main") == RemoteFileStatus.NO_BACKUP


# ---------------------------------------------------------------------------
# local_branch_exists / remote_branch_exists
# ---------------------------------------------------------------------------


def test_local_branch_exists(git_service):
    init_service_with_commit(git_service)
    assert git_service.local_branch_exists("main") is True
    assert git_service.local_branch_exists("does-not-exist") is False


def test_remote_branch_exists(tmp_path):
    remote = create_populated_remote(tmp_path)
    service = make_git_service(tmp_path / "svc")
    attach_remote(service, remote)
    assert service.remote_branch_exists("origin", "main") is True
    assert service.remote_branch_exists("origin", "ghost") is False
    assert service.remote_branch_exists("missing", "main") is False


# ---------------------------------------------------------------------------
# fetch / set_remote
# ---------------------------------------------------------------------------


def test_set_remote_builds_authenticated_url(monkeypatch, git_service):
    commands = []
    monkeypatch.setattr(
        git_service, "_run_command", lambda command, cwd: commands.append(command) or ""
    )
    git_service.set_remote("origin")
    add_command = next(c for c in commands if c.startswith("git remote add origin"))
    expected_url = "http://oauth:test-token@example.com/services/grader/git/21wle1/1/user"
    assert expected_url in add_command


def test_set_remote_updates_existing_remote(monkeypatch, git_service):
    commands = []

    def fake_run(command, cwd):
        commands.append(command)
        if command.startswith("git remote add"):
            raise GitError(128, "remote already exists")
        return ""

    monkeypatch.setattr(git_service, "_run_command", fake_run)
    git_service.set_remote("origin")
    assert any(c.startswith("git remote set-url origin") for c in commands)


def test_fetch_all(tmp_path):
    remote = create_populated_remote(tmp_path)
    service = make_git_service(tmp_path / "svc")
    attach_remote(service, remote)
    # fetch --all succeeds silently
    service.fetch_all()
    assert service.remote_branch_exists("origin", "main")


# ---------------------------------------------------------------------------
# push / pull
# ---------------------------------------------------------------------------


def test_push_pushes_to_remote(tmp_path):
    remote = create_populated_remote(tmp_path)
    service = make_git_service(tmp_path / "svc")
    attach_remote(service, remote)
    (service.path / "extra.txt").write_text("extra")
    service.commit("extra commit", selected_files=["extra.txt"])
    service.push("origin", force=True)
    remote_log = run_git("log", "--pretty=%s", cwd=remote)
    assert "extra commit" in remote_log


def test_pull_force_resets_local_to_remote(tmp_path):
    remote = create_populated_remote(tmp_path)
    service = make_git_service(tmp_path / "svc")
    attach_remote(service, remote)
    # Make a dirty local change that should be discarded on a forced pull.
    (service.path / "assignment.ipynb").write_text("# local dirt")
    # Advance the remote clone with a fresh commit so the pull has something to do.
    work = tmp_path / "clone"
    (work / "assignment.ipynb").write_text("# from remote")
    run_git("add", "assignment.ipynb", cwd=work)
    run_git("commit", "-m", "remote update", cwd=work)
    run_git("push", "origin", "main", cwd=work)

    service.pull("origin", branch="main", force=True)

    assert (service.path / "assignment.ipynb").read_text() == "# from remote"


def test_pull_raises_when_remote_missing(git_service):
    git_service.init()
    with pytest.raises(GitError) as exc_info:
        git_service.pull("origin", branch="main", force=True)
    assert exc_info.value.code == 404


def test_pull_regular_checkout(tmp_path):
    remote = create_populated_remote(tmp_path)
    service = make_git_service(tmp_path / "svc")
    attach_remote(service, remote)
    work = tmp_path / "clone"
    (work / "assignment.ipynb").write_text("# updated remotely")
    run_git("add", "assignment.ipynb", cwd=work)
    run_git("commit", "-m", "remote update", cwd=work)
    run_git("push", "origin", "main", cwd=work)

    service.pull("origin", branch="main", force=False)

    assert (service.path / "assignment.ipynb").read_text() == "# updated remotely"


# ---------------------------------------------------------------------------
# clone
# ---------------------------------------------------------------------------


def test_clone_orchestrates_init_set_remote_and_pull(tmp_path):
    remote = create_populated_remote(tmp_path)
    service = make_git_service(tmp_path / "svc")
    service.set_remote = lambda origin, additional_path="": run_git(
        "remote", "add", origin, str(remote), cwd=service.path
    )
    service.clone("origin", force=True)
    assert (service.path / "assignment.ipynb").exists()
    assert service.is_git()


# ---------------------------------------------------------------------------
# go_to_commit / undo_commit / revert
# ---------------------------------------------------------------------------


def test_go_to_commit_checks_out_commit(git_service):
    init_service_with_commit(git_service, "first", files=[("a.txt", "one")])
    init_service_with_commit(git_service, "second", files=[("b.txt", "two")])
    first = run_git("rev-parse", "HEAD~1", cwd=git_service.path).strip()
    git_service.go_to_commit(first)
    assert run_git("rev-parse", "HEAD", cwd=git_service.path).strip() == first


def test_undo_commit_removes_latest_commit(git_service):
    init_service_with_commit(git_service, "first", files=[("a.txt", "one")])
    first = run_git("rev-parse", "HEAD", cwd=git_service.path).strip()
    init_service_with_commit(git_service, "second", files=[("b.txt", "two")])
    git_service.undo_commit(1)
    assert run_git("rev-parse", "HEAD", cwd=git_service.path).strip() == first


def test_revert_to_head_undoes_local_changes(git_service):
    first = init_service_with_commit(git_service, "first", files=[("a.txt", "one")])
    (git_service.path / "a.txt").write_text("two")
    assert (git_service.path / "a.txt").read_text() == "two"
    git_service.revert(first)
    assert (git_service.path / "a.txt").read_text() == "one"


def test_revert_to_previous_commit_creates_revert_commit(git_service):
    first = init_service_with_commit(git_service, "first", files=[("a.txt", "one")])
    init_service_with_commit(git_service, "second", files=[("a.txt", "two")])
    git_service.revert(first)
    log = run_git("log", "--pretty=%s", cwd=git_service.path)
    assert f"reverting to {first}" in log
    assert (git_service.path / "a.txt").read_text() == "one"


# ---------------------------------------------------------------------------
# get_log
# ---------------------------------------------------------------------------


def test_get_log_returns_newest_commit_first(git_service):
    init_service_with_commit(git_service, "first", files=[("a.txt", "one")])
    init_service_with_commit(git_service, "second", files=[("b.txt", "two")])
    logs = git_service.get_log(10)
    assert logs[0]["commit_msg"] == "second"
    assert logs[1]["commit_msg"] == "first"
    assert logs[0]["author"] == "Test Author"
    assert logs[0]["pre_commit"] == logs[1]["commit"]


def test_get_log_respects_history_count(git_service):
    for i in range(3):
        init_service_with_commit(git_service, f"commit-{i}", files=[(f"f{i}.txt", str(i))])
    assert len(git_service.get_log(2)) == 2


# ---------------------------------------------------------------------------
# delete_repo_contents / copy_repo_contents
# ---------------------------------------------------------------------------


def test_delete_repo_contents_keeps_git_dir(git_service):
    git_service.init()
    (git_service.path / "a.txt").write_text("a")
    (git_service.path / "sub").mkdir()
    (git_service.path / "sub" / "b.txt").write_text("b")
    git_service.delete_repo_contents(include_git=False)
    assert not (git_service.path / "a.txt").exists()
    assert not (git_service.path / "sub").exists()
    assert git_service.is_git()


def test_delete_repo_contents_with_git_dir_removes_repo(git_service):
    git_service.init()
    (git_service.path / "a.txt").write_text("a")
    git_service.delete_repo_contents(include_git=True)
    assert not git_service.is_git()


def test_copy_repo_contents_copies_all_files(git_service, tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.txt").write_text("a")
    (src / "b.txt").write_text("b")
    (src / ".git").mkdir()
    git_service.copy_repo_contents(str(src))
    assert (git_service.path / "a.txt").exists()
    assert (git_service.path / "b.txt").exists()
    assert not (git_service.path / ".git").exists()


def test_copy_repo_contents_selected_files_only(git_service, tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.txt").write_text("a")
    (src / "b.txt").write_text("b")
    git_service.copy_repo_contents(str(src), selected_files=["a.txt"])
    assert (git_service.path / "a.txt").exists()
    assert not (git_service.path / "b.txt").exists()


# ---------------------------------------------------------------------------
# git_version
# ---------------------------------------------------------------------------


def test_git_version_returns_tuple(git_service):
    version = git_service.git_version
    assert isinstance(version, tuple)
    assert len(version) >= 2
    assert all(isinstance(part, int) for part in version)


def test_git_version_is_cached(monkeypatch, git_service):
    calls = []
    real = git_service._run_command
    monkeypatch.setattr(
        git_service,
        "_run_command",
        lambda command, cwd: calls.append(command) or real(command, cwd),
    )
    git_service.git_version
    git_service.git_version
    assert calls.count("git --version") == 1


def test_git_version_returns_empty_on_error(monkeypatch, git_service):
    monkeypatch.setattr(
        git_service, "_run_command", lambda command, cwd: (_ for _ in ()).throw(GitError())
    )
    assert git_service.git_version == ()
