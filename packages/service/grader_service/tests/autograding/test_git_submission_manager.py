import pytest

from grader_service.autograding.git_manager import GitSubmissionManager
from grader_service.handlers import GitRepoType


def test_git_repo_path_with_fabricated_user_name(submission_123, tmp_path):
    """Make sure that a fabricated username cannot be used to create a git repo in a wrong directory."""
    submission_123.user.name = "../../../../../"

    grader_service_dir = str(tmp_path)
    git_manager = GitSubmissionManager(grader_service_dir, submission_123)

    with pytest.raises(PermissionError, match="Invalid repository path"):
        git_manager._get_repo_path(GitRepoType.USER)
