from typing import Optional

from traitlets import Unicode

from grader_service.handlers.git.base import RepoType, GitBaseHandler, RPCPathMixin, InfoRefsPathMixin
from grader_service.handlers.git.local import GitServer
from grader_service.orm import User, Lecture, Assignment, Submission


class GitLabHandler(GitBaseHandler):
    @property
    def git_location(self):
        return GitLabServer.instance().git_location(self.repo_type, self.user, self.assignment, self.submission)

    def repo_exists(self) -> bool:
        pass

    def create_repo(self):
        pass


# Actual implementations of handlers
class RPCGitLabHandler(RPCPathMixin, GitLabHandler):
    pass


class InfoRefsGitLabHandler(InfoRefsPathMixin, GitLabHandler):
    pass


class GitLabServer(GitServer):
    gitlab_url = Unicode().tag(config=True)

    def register_handlers(self):
        pass

    def git_location(self, repo_type: RepoType, user: User, assignment: Assignment,
                     submission: Optional[Submission] = None) -> str:
        pass
