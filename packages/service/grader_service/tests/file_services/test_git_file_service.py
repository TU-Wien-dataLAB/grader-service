import shutil
import subprocess
from unittest.mock import patch

import pytest

from grader_service.file_services.base_file_service import FileServiceError
from grader_service.file_services.git_file_service import GitFileService, construct_git_dir
from grader_service.handlers.handler_utils import GitRepoType
from grader_service.orm.submission import AutoStatus, ManualStatus
from grader_service.tests.handlers.db_util import create_user_submission_with_repo


@pytest.fixture
def git_file_service(tmpdir, grader_service):
    """Create a GitFileService instance with proper directory structure."""
    service = GitFileService(grader_service_dir=grader_service.grader_service_dir)
    yield service


@pytest.fixture
def setup_repos(git_file_service, submission_123):
    """Set up basic repository structure for testing."""
    assignment = submission_123.assignment
    lecture_code = assignment.lecture.code

    # Create release repo
    release_path = construct_git_dir(
        git_file_service.gitbase, GitRepoType.RELEASE, lecture_code, assignment.id
    )
    git_file_service.create_bare_repo(release_path)

    # Create user repo
    user_path = construct_git_dir(
        git_file_service.gitbase,
        GitRepoType.USER,
        lecture_code,
        assignment.id,
        username=submission_123.user.name,
    )
    git_file_service.create_bare_repo(user_path)

    yield {"release": release_path, "user": user_path}


@pytest.fixture
def setup_repos_with_release_files(git_file_service, setup_repos):
    """Add a commit with a file to the release repo."""
    remote_path = setup_repos["release"]
    clone_path = git_file_service.tmpbase / "release"
    clone_path.mkdir(parents=True, exist_ok=True)
    git_file_service._run_git(
        ["git", "clone", remote_path, clone_path], cwd=git_file_service.tmpbase
    )
    file_path = clone_path / "assignment.ipynb"
    file_path.touch()
    git_file_service._run_git(["git", "add", file_path], cwd=clone_path)
    git_file_service._run_git(["git", "commit", "-m", "Add assignment notebook"], cwd=clone_path)
    git_file_service._run_git(["git", "push", "-u", "origin", "main"], cwd=clone_path)
    shutil.rmtree(clone_path)

    yield setup_repos


# =============== construct_git_dir tests ===============


def test_construct_git_dir_source_repo(assignment_123, tmp_path):
    """Test path construction for SOURCE repo type."""
    gitbase = tmp_path / "git"
    lecture_code = assignment_123.lecture.code
    path = construct_git_dir(gitbase, GitRepoType.SOURCE, lecture_code, assignment_123.id)

    expected = gitbase / lecture_code / str(assignment_123.id) / GitRepoType.SOURCE
    assert path == expected


def test_construct_git_dir_release_repo(assignment_123, tmp_path):
    """Test path construction for RELEASE repo type."""
    gitbase = tmp_path / "git"
    lecture_code = assignment_123.lecture.code
    path = construct_git_dir(gitbase, GitRepoType.RELEASE, lecture_code, assignment_123.id)

    expected = gitbase / lecture_code / str(assignment_123.id) / GitRepoType.RELEASE
    assert path == expected


def test_construct_git_dir_user_repo(assignment_123, tmp_path):
    """Test path construction for USER repo type."""
    gitbase = tmp_path / "git"
    lecture_code = assignment_123.lecture.code
    username = "test_user"
    path = construct_git_dir(
        gitbase, GitRepoType.USER, lecture_code, assignment_123.id, username=username
    )

    expected = gitbase / lecture_code / str(assignment_123.id) / GitRepoType.USER / username
    assert path == expected


def test_construct_git_dir_edit_repo_requires_submission_id(assignment_123, tmp_path):
    """Test that EDIT repo type requires submission_id."""
    lecture_code = assignment_123.lecture.code

    with pytest.raises(ValueError, match="Missing submission_id"):
        construct_git_dir(tmp_path / "git", GitRepoType.EDIT, lecture_code, assignment_123.id)


def test_construct_git_dir_edit_repo(submission_123, tmp_path):
    """Test path construction for EDIT repo type."""
    gitbase = tmp_path / "git"
    assign = submission_123.assignment
    lecture_code = assign.lecture.code
    path = construct_git_dir(gitbase, GitRepoType.EDIT, lecture_code, assign.id, submission_123.id)

    expected = gitbase / lecture_code / str(assign.id) / GitRepoType.EDIT / str(submission_123.id)
    assert path == expected


@pytest.mark.parametrize(
    "repo_type", [GitRepoType.USER, GitRepoType.AUTOGRADE, GitRepoType.FEEDBACK]
)
def test_construct_git_dir_repo_types_require_username(assignment_123, tmp_path, repo_type):
    """Test that certain repo types require submission_id."""
    lecture_code = assignment_123.lecture.code

    with pytest.raises(ValueError, match="Missing username"):
        construct_git_dir(tmp_path / "git", repo_type, lecture_code, assignment_123.id)


def test_construct_git_dir_autograde_repo(submission_123, tmp_path):
    """Test path construction for AUTOGRADE repo type."""
    gitbase = tmp_path / "git"
    assign = submission_123.assignment
    lecture_code = assign.lecture.code
    username = "test_user"
    path = construct_git_dir(
        gitbase, GitRepoType.AUTOGRADE, lecture_code, assign.id, username=username
    )

    expected = gitbase / lecture_code / str(assign.id) / GitRepoType.AUTOGRADE / "user" / username
    assert path == expected


def test_construct_git_dir_feedback_repo(submission_123, tmp_path):
    """Test path construction for FEEDBACK repo type."""
    gitbase = tmp_path / "git"
    assign = submission_123.assignment
    lecture_code = assign.lecture.code
    username = "test_user"
    path = construct_git_dir(
        gitbase, GitRepoType.FEEDBACK, lecture_code, assign.id, username=username
    )

    expected = gitbase / lecture_code / str(assign.id) / GitRepoType.FEEDBACK / "user" / username
    assert path == expected


def test_construct_git_dir_path_validation_prevents_traversal(assignment_123, tmp_path):
    """Test that path traversal attempts are blocked."""
    lecture_code = "../.."

    with pytest.raises(ValueError, match="Invalid path"):
        construct_git_dir(tmp_path / "git", GitRepoType.SOURCE, lecture_code, assignment_123.id)


# =============== is_bare_git_dir tests ===============


def test_is_bare_git_dir_returns_true_for_bare_repo(git_file_service, setup_repos):
    """Test detection of bare git repository."""
    bare_repo_path = setup_repos["release"]

    result = git_file_service.is_bare_git_dir(bare_repo_path)

    assert result is True


def test_is_bare_git_dir_returns_false_for_non_bare_repo(git_file_service, setup_repos, tmp_path):
    """Test that non-bare git repos are not detected as bare."""
    bare_repo_path = setup_repos["release"]
    clone_dir = tmp_path / "tmp"
    clone_dir.mkdir()
    git_file_service._run_git(["git", "clone", bare_repo_path], cwd=clone_dir)

    result = git_file_service.is_bare_git_dir(clone_dir)

    assert result is False


def test_is_bare_git_dir_returns_false_for_non_git_dir(git_file_service, tmp_path):
    """Test that non-git directories are not detected as bare repos."""
    non_git_dir = tmp_path / "not_a_repo"
    non_git_dir.mkdir()

    result = git_file_service.is_bare_git_dir(non_git_dir)

    assert result is False


def test_is_bare_git_dir_returns_false_for_nonexistent_path(git_file_service):
    """Test that nonexistent paths return False."""
    nonexistent_path = git_file_service.gitbase / "nonexistent"

    result = git_file_service.is_bare_git_dir(nonexistent_path)

    assert result is False


# =============== create_bare_repo tests ===============


def test_create_bare_repo_creates_directory_and_initializes(git_file_service, tmp_path):
    """Test bare repo creation."""
    repo_path = tmp_path / "test_repo"

    git_file_service.create_bare_repo(repo_path)

    assert repo_path.exists()
    assert git_file_service.is_bare_git_dir(repo_path)


def test_create_bare_repo_recreates_existing_when_flag_set(git_file_service, tmp_path):
    """Test that existing repo is recreated when recreate_dir=True."""
    repo_path = tmp_path / "test_repo"
    git_file_service.create_bare_repo(repo_path)

    # Create a file in the repo
    marker_file = repo_path / "marker.txt"
    marker_file.touch()
    assert marker_file.exists()

    # Recreate should remove the file
    git_file_service.create_bare_repo(repo_path, recreate_dir=True)

    assert not marker_file.exists()
    assert git_file_service.is_bare_git_dir(repo_path)


def test_create_bare_repo_custom_branch(git_file_service, tmp_path):
    """Test bare repo creation with custom initial branch."""
    repo_path = tmp_path / "test_repo"
    custom_branch = "develop"

    git_file_service.create_bare_repo(repo_path, initial_branch=custom_branch)

    # Verify the branch was created
    result = subprocess.run(
        ["git", "branch", "--show-current"], cwd=repo_path, capture_output=True, text=True
    )
    assert custom_branch in result.stdout


# =============== validate_submission_exists tests ===============


def test_validate_submission_exists_raises_when_repo_not_found(git_file_service, submission_123):
    """Test error when user repository doesn't exist."""
    with pytest.raises(FileServiceError, match="User git repository not found"):
        git_file_service.validate_submission_exists(
            submission_123.commit_hash, submission_123.assignment, submission_123.user.name
        )


def test_validate_submission_exists_raises_when_commit_not_found(
    git_file_service, submission_123, setup_repos
):
    """Test error when user repo exists but submission commit is not in main branch."""

    with pytest.raises(FileServiceError, match="Submission commit not found"):
        git_file_service.validate_submission_exists(
            "9" * 40, submission_123.assignment, submission_123.user.name
        )


# =============== init_user_files tests ===============


def test_init_user_files_raises_when_release_not_exists(git_file_service, submission_123):
    """Test error when release repository doesn't exist."""
    with pytest.raises(FileNotFoundError, match="release repository does not exist"):
        git_file_service.init_user_files(
            submission_123.assignment, submission_123.user.name, "Initial commit"
        )


def test_init_user_files_raises_when_user_repo_not_exists(
    git_file_service, submission_123, setup_repos
):
    """Test error when user repository doesn't exist."""
    shutil.rmtree(setup_repos["user"])

    with pytest.raises(FileNotFoundError, match="user submission repository"):
        git_file_service.init_user_files(
            submission_123.assignment, submission_123.user.name, "Initial commit"
        )


def test_init_user_files(git_file_service, submission_123, setup_repos_with_release_files):
    """Test successful copying of release files to a new user repo."""
    l_code = submission_123.assignment.lecture.code
    a_id = submission_123.assignment.id
    username = submission_123.user.name
    tmp_base = git_file_service.tmpbase / l_code / str(a_id) / username
    msg = "Test initial commit"

    git_file_service.init_user_files(submission_123.assignment, username, msg)

    user_remote = setup_repos_with_release_files["user"]
    commit_log = subprocess.run(
        ["git", "log", "--oneline"], cwd=user_remote, capture_output=True, text=True
    ).stdout
    assert msg in commit_log
    # Temp directory should be cleaned up
    assert not tmp_base.exists()


# =============== fetch_files tests ===============


@pytest.mark.parametrize(
    "repo_type", [GitRepoType.SOURCE, GitRepoType.RELEASE, GitRepoType.FEEDBACK]
)
def test_fetch_files_raises_for_invalid_repo_type(
    git_file_service, submission_123, tmp_path, repo_type
):
    """Test error when invalid repo type is provided."""
    with pytest.raises(ValueError, match="Cannot fetch submission files"):
        git_file_service.fetch_files(tmp_path, repo_type, submission_123)


def test_fetch_files_user_repo_checks_out_commit(
    git_file_service, submission_123, setup_repos, tmp_path
):
    """Test that fetching from USER repo checks out the submission commit."""
    input_dir = tmp_path / "input"
    input_dir.mkdir()

    with patch.object(git_file_service, "_run_git") as mock_run_git:
        git_file_service.fetch_files(input_dir, GitRepoType.USER, submission_123)

    # Verify checkout command was called with commit hash
    checkout_calls = [call for call in mock_run_git.call_args_list if "checkout" in str(call)]
    assert len(checkout_calls) == 1
    assert submission_123.commit_hash in checkout_calls[0].args[0]


def test_fetch_files_autograde_uses_submission_branch_when_graded(
    git_file_service, submission_123, setup_repos, tmp_path
):
    """Test that autograde repo uses submission-specific branch when already graded."""
    submission_123.auto_status = AutoStatus.AUTOMATICALLY_GRADED
    input_dir = tmp_path / "input"
    input_dir.mkdir()

    with patch.object(git_file_service, "_run_git") as mock_run_git:
        git_file_service.fetch_files(input_dir, GitRepoType.AUTOGRADE, submission_123)

    # Verify pull command uses submission-specific branch
    pull_calls = [call for call in mock_run_git.call_args_list if "pull" in str(call)]
    assert len(pull_calls) == 1
    assert f"submission_{submission_123.commit_hash}" in pull_calls[0].args[0]


def test_fetch_files_autograde_falls_back_to_user_when_not_graded(
    git_file_service, submission_123, setup_repos, tmp_path
):
    """Test that autograde falls back to USER repo when not yet graded."""
    submission_123.auto_status = AutoStatus.NOT_GRADED
    submission_123.manual_status = ManualStatus.MANUALLY_GRADED
    input_dir = tmp_path / "input"
    input_dir.mkdir()

    with patch.object(git_file_service, "_run_git") as mock_run_git:
        git_file_service.fetch_files(input_dir, GitRepoType.AUTOGRADE, submission_123)

    # Should have pulled from USER repo, main branch instead
    pull_calls = [call for call in mock_run_git.call_args_list if "pull" in str(call)]
    assert len(pull_calls) == 1

    a_id = submission_123.assignment.id
    l_code = submission_123.assignment.lecture.code
    username = submission_123.user.name
    user_repo_path = construct_git_dir(
        git_file_service.gitbase, GitRepoType.USER, l_code, a_id, username=username
    )
    assert user_repo_path in pull_calls[0].args[0]  # git command as a list
    assert "main" in pull_calls[0].args[0]
    assert pull_calls[0].args[1] == input_dir  # path where the command was executed

    # Verify checkout command was called with commit hash
    checkout_calls = [call for call in mock_run_git.call_args_list if "checkout" in str(call)]
    assert len(checkout_calls) == 1
    assert submission_123.commit_hash in checkout_calls[0].args[0]


def test_fetch_files_from_user_repo(git_file_service, sql_alchemy_engine, default_user, tmp_path):
    """Test successful fetching of files."""
    # Preparation: initiate the user repository, create and commit a file "submission.ipynb"
    sub = create_user_submission_with_repo(
        sql_alchemy_engine,
        git_file_service.gitbase,
        student=default_user,
        assignment_id=1,
        lecture_code="21wle1",
    )

    input_dir = tmp_path / "input"
    input_dir.mkdir()

    git_file_service.fetch_files(input_dir, GitRepoType.USER, sub)

    assert (input_dir / "submission.ipynb").exists()
    is_inside_work_tree = subprocess.run(
        [git_file_service.git_executable, "rev-parse", "--is-inside-work-tree"],
        cwd=input_dir,
        capture_output=True,
    ).stdout.decode("utf-8")
    assert "true" in is_inside_work_tree


# =============== edit_submission tests ===============


@patch("grader_service.file_services.git_file_service.GitFileService.fetch_files")
@patch("grader_service.file_services.git_file_service.GitFileService._run_git_async")
async def test_edit_submission_raises_when_user_repo_not_exists(
    mock_run_async, mock_fetch, git_file_service, submission_123
):
    """Test error when user repository doesn't exist for edit."""
    with pytest.raises(FileNotFoundError, match="user submission repository"):
        await git_file_service.edit_submission(submission_123)


async def test_edit_submission(git_file_service, sql_alchemy_engine, default_user):
    """Test creating an EDIT repository."""
    # Preparation: initiate the user repository, create and commit a file "submission.ipynb"
    sub = create_user_submission_with_repo(
        sql_alchemy_engine,
        git_file_service.gitbase,
        student=default_user,
        assignment_id=1,
        lecture_code="21wle1",
    )

    a_id = sub.assignment.id
    l_code = sub.assignment.lecture.code
    tmp_base = git_file_service.tmpbase / l_code / str(a_id) / "edit" / str(sub.id)

    remote_path_edit = construct_git_dir(
        git_file_service.gitbase, GitRepoType.EDIT, l_code, a_id, submission_id=sub.id
    )
    assert not remote_path_edit.exists()

    await git_file_service.edit_submission(sub)

    # Remote EDIT repo should exist and contain an initial commit
    assert git_file_service.is_bare_git_dir(remote_path_edit)
    commit_log = subprocess.run(
        ["git", "log", "--oneline"], cwd=remote_path_edit, capture_output=True, text=True
    ).stdout
    assert "Initial commit" in commit_log
    # Temp directory should be cleaned up
    assert not tmp_base.exists()


# =============== delete_lecture_files tests ===============


def test_delete_lecture_files_removes_git_and_tmp_dirs(git_file_service, assignment_123):
    """Test that lecture deletion removes both git and tmp directories."""
    lecture_code = assignment_123.lecture.code

    # Create directories
    git_lecture_path = git_file_service.gitbase / lecture_code
    tmp_lecture_path = git_file_service.tmpbase / lecture_code
    git_lecture_path.mkdir(parents=True)
    tmp_lecture_path.mkdir(parents=True)

    git_file_service.delete_lecture_files(assignment_123.lecture)

    assert not git_lecture_path.exists()
    assert not tmp_lecture_path.exists()


def test_delete_lecture_files_ignores_missing_dirs(git_file_service, assignment_123):
    """Test that deletion doesn't fail when directories don't exist."""
    lecture_code = assignment_123.lecture.code

    # Don't create the directories
    git_lecture_path = git_file_service.gitbase / lecture_code
    tmp_lecture_path = git_file_service.tmpbase / lecture_code
    assert not git_lecture_path.exists()
    assert not tmp_lecture_path.exists()

    git_file_service.delete_lecture_files(assignment_123.lecture)


def test_delete_lecture_files_validation_prevents_traversal(git_file_service, assignment_123):
    assignment_123.lecture.code = "../.."

    with pytest.raises(ValueError, match="Invalid path"):
        git_file_service.delete_lecture_files(assignment_123.lecture)


# =============== delete_assignment_files tests ===============


def test_delete_assignment_files_removes_assignment_dirs(git_file_service, assignment_123):
    """Test that assignment deletion removes both git and tmp assignment directories."""
    lecture_code = assignment_123.lecture.code
    assignment_id = str(assignment_123.id)

    # Create directories
    git_assignment_path = git_file_service.gitbase / lecture_code / assignment_id
    tmp_assignment_path = git_file_service.tmpbase / lecture_code / assignment_id
    git_assignment_path.mkdir(parents=True)
    tmp_assignment_path.mkdir(parents=True)

    git_file_service.delete_assignment_files(assignment_123, assignment_123.lecture)

    assert not git_assignment_path.exists()
    assert not tmp_assignment_path.exists()
    assert (git_file_service.gitbase / lecture_code).exists()
    assert (git_file_service.tmpbase / lecture_code).exists()


# =============== delete_submission_files tests ===============


def test_delete_submission_files_removes_user_and_submission_dirs(git_file_service, submission_123):
    """Test that submission deletion removes submission-specific directories."""
    l_code = submission_123.assignment.lecture.code
    a_id = str(submission_123.assignment.id)
    username = submission_123.user.name
    s_id = submission_123.id

    # Create submission-specific directories in gitbase and tmpbase
    submission_dirs = []
    assignment_dirs = []
    for repo_type in GitRepoType:
        repo_path = construct_git_dir(
            git_file_service.gitbase, repo_type, l_code, a_id, submission_id=s_id, username=username
        )
        repo_path.mkdir(parents=True)
        if repo_type in [GitRepoType.SOURCE, GitRepoType.RELEASE]:
            assignment_dirs.append(repo_path)
            tmp_path = git_file_service.tmpbase / l_code / a_id / repo_type
            assignment_dirs.append(tmp_path)
        else:
            submission_dirs.append(repo_path)
            tmp_path = git_file_service.tmpbase / l_code / a_id / repo_type / username
            submission_dirs.append(tmp_path)
        tmp_path.mkdir(parents=True)

    git_file_service.delete_submission_files(submission_123)

    for submission_path in submission_dirs:
        assert not submission_path.exists()
    for assignment_path in assignment_dirs:
        assert assignment_path.exists()


def test_delete_submission_files_only_removes_target_submission(
    git_file_service, submission_123, setup_repos
):
    """Test that only the target submission is deleted, not others."""
    l_code = submission_123.assignment.lecture.code
    a_id = str(submission_123.assignment.id)

    # Create another user's repo
    other_username = "other_user"
    other_user_path = construct_git_dir(
        git_file_service.gitbase, GitRepoType.USER, l_code, a_id, username=other_username
    )
    git_file_service.create_bare_repo(other_user_path)

    git_file_service.delete_submission_files(submission_123)

    assert other_user_path.exists()
