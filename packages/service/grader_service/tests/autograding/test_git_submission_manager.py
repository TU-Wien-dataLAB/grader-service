# import pytest
#
# from grader_service.autograding.git_manager import GitSubmissionManager
# from grader_service.handlers import GitRepoType
#
#
# def test_git_repo_path_with_fabricated_user_name(grader_service, submission_123, tmp_path):
#     """Make sure that a fabricated username cannot be used to create a git repo in a wrong directory."""
#     # from grader_service import GraderService
#     #
#     # GraderService.grader_service_dir = app.grader_service_dir
#     # grader_service = GraderService.instance()
#     # grader_service.grader_service_dir = app.grader_service_dir
#
#     submission_123.user.name = "../../../../../"
#
#     grader_service_dir = str(tmp_path)
#     git_manager = GitSubmissionManager(submission_123)
#
#     with pytest.raises(ValueError, match="Invalid path"):
#         git_manager._get_repo_path(GitRepoType.USER)
