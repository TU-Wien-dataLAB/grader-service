# Copyright (c) 2022, TU Wien
# All rights reserved.
#
import enum
import logging
import os
import posixpath
import shlex
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse

from grader_service.handlers import GitRepoType
from traitlets.config.configurable import Configurable
from traitlets.traitlets import Unicode


class GitError(Exception):
    def __init__(self, code: int = 500, error: str = "Unknown Error"):
        self.code = code
        self.error = error
        super().__init__(error)


class RemoteFileStatus(enum.Enum):
    UP_TO_DATE = 1
    PULL_NEEDED = 2
    PUSH_NEEDED = 3
    DIVERGENT = 4
    NO_REMOTE_REPO = 5


class GitService(Configurable):
    DEFAULT_HOST_URL = "http://127.0.0.1:4010"
    DEFAULT_GIT_URL_PREFIX = "/services/grader/git"
    _git_version = None

    git_access_token = Unicode(os.environ.get("GRADER_API_TOKEN"), allow_none=False).tag(
        config=True
    )
    git_service_url = Unicode(
        os.environ.get("GRADER_HOST_URL", DEFAULT_HOST_URL)
        + os.environ.get("GRADER_GIT_PREFIX", DEFAULT_GIT_URL_PREFIX),
        allow_none=False,
    ).tag(config=True)

    def __init__(
        self,
        server_root_dir: str,
        lecture_code: str,
        assignment_id: int,
        repo_type: GitRepoType,
        force_user_repo: bool = False,
        sub_id: Optional[int] = None,
        username: Optional[str] = None,
        log=logging.getLogger("gitservice"),
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.log = log
        self.git_root_dir = server_root_dir
        self.lecture_code = lecture_code
        self.assignment_id = assignment_id
        self.repo_type = repo_type

        self.path = self._determine_repo_path(force_user_repo, sub_id, username)
        os.makedirs(self.path, exist_ok=True)

        self._initialize_git_logging()

    def _determine_repo_path(
        self, force_user_repo: bool, sub_id: Optional[int], username: Optional[str]
    ) -> str:
        """Determine the path for the git repository based on the type."""
        if self.repo_type == GitRepoType.USER or force_user_repo:
            # For repo type USER, the subdirectory is called `assignments` (for historical reasons).
            return os.path.join(
                self.git_root_dir, self.lecture_code, "assignments", str(self.assignment_id)
            )
        elif self.repo_type == GitRepoType.EDIT:
            if username is not None:
                return os.path.join(
                    self.git_root_dir,
                    self.lecture_code,
                    "create",
                    str(self.assignment_id),
                    username,
                )
            else:
                return os.path.join(
                    self.git_root_dir,
                    self.lecture_code,
                    self.repo_type,
                    str(self.assignment_id),
                    str(sub_id),
                )
        return os.path.join(
            self.git_root_dir, self.lecture_code, self.repo_type, str(self.assignment_id)
        )

    def _initialize_git_logging(self):
        """Initialize logging related to git configuration."""
        self.log.info(f"New git service working in {self.path}")
        self.git_http_scheme, self.git_remote_url = self._parse_git_service_url()
        self.log.info(f"git_service_url: {self.git_service_url}")

    def _parse_git_service_url(self) -> Tuple[str, str]:
        """Parse the git service URL into scheme and remote URL."""
        url_parsed = urlparse(self.git_service_url)
        return url_parsed.scheme, f"{url_parsed.netloc}{url_parsed.path}"

    def push(self, origin: str, force: bool = False):
        """Push commits to the remote repository.

        Args:
            origin (str): The remote repository.
            force (bool): Whether to force push. Defaults to False.
        """
        self.log.info(f"Pushing to remote {origin} at {self.path}")
        self._run_command(f"git push {origin} main" + (" --force" if force else ""), cwd=self.path)

    def set_remote(self, origin: str, additional_path: str = ""):
        """Set or update the remote repository.

        Args:
            origin (str): The remote name.
            additional_path (str): Optional additional path for the remote.
        """
        url_path = posixpath.join(
            self.git_remote_url, self.lecture_code, str(self.assignment_id), self.repo_type
        )
        url = (
            f"{self.git_http_scheme}://oauth:{self.git_access_token}@"
            f"{posixpath.join(url_path, additional_path)}"
        )
        self.log.info(f"Setting remote {origin} for {self.path} to {url}")
        try:
            self._run_command(f"git remote add {origin} {url}", cwd=self.path)
        except GitError:
            self.log.warning(f"Remote {origin} already exists. Updating URL.")
            self._run_command(f"git remote set-url {origin} {url}", cwd=self.path)

    def switch_branch(self, branch: str):
        """Switch to the specified branch.

        Args:
            branch (str): The branch name.
        """
        self.log.info(f"Fetching all branches at {self.path}")
        self._run_command("git fetch --all", cwd=self.path)
        self.log.info(f"Switching to branch {branch} at {self.path}")
        self._run_command(f"git checkout {branch}", cwd=self.path)

    def fetch_all(self):
        self.log.info(f"Fetching all at path {self.path}")
        self._run_command("git fetch --all", cwd=self.path)

    def pull(self, origin: str, branch: str = "main", force: bool = False):
        """Pull changes from the remote repository.

        Args:
            origin (str): The remote repository.
            branch (str): The branch to pull from. Defaults to "main".
            force (bool): Whether to force the pull. Defaults to False.
        """
        self.log.info(f"Pulling from {origin}/{branch} at {self.path}")
        if not self.remote_branch_exists(origin, branch):
            raise GitError(
                code=404,
                error="Remote repository not found. Please ensure your assignment is pushed "
                "to the repository before proceeding.",
            )

        if force:
            # clean local changes
            command = "git clean -fd"
            self._run_command(command, cwd=self.path)
            # fetch info
            command = f"git fetch {origin}"
            self._run_command(command, cwd=self.path)
            # reset to branch head
            command = f"git reset --hard {origin}/{branch}"
            self._run_command(command, cwd=self.path)
        else:
            # just pull the branch
            command = f"git pull {origin} {branch}"
            self._run_command(command, cwd=self.path)

    def init(self, force: bool = False):
        """Initialize a local repository.

        Args:
            force (bool): Whether to force initialization. Defaults to False.
        """
        if not self.is_git() or force:
            self.log.info(f"Initializing git repository at {self.path}")
            command = "git init -b main" if self.git_version >= (2, 28) else "git init"
            self._run_command(command, cwd=self.path)

    def go_to_commit(self, commit_hash):
        self.log.info(f"Show commit with hash {commit_hash}")
        self._run_command(f"git checkout {commit_hash}", cwd=self.path)

    def undo_commit(self, n: int = 1) -> None:
        self.log.info(f"Undoing {n} commit(s)")
        self._run_command(f"git reset --mixed HEAD~{n}", cwd=self.path)
        self._run_command("git gc", cwd=self.path)

    def revert(self, commit_hash: str):
        """Revert the repository to a previous commit.
        If the commit hash equal the HEAD commit, all local changes will be undone.
        Otherwise, the files will be reset to the specified commit.

        Args:
            commit_hash (str): The hash of the commit to revert to.
        """
        self.log.info(f"Reverting to {commit_hash}")
        if commit_hash == self._run_command("git rev-parse HEAD", cwd=self.path).strip():
            # If the commit hash is the HEAD commit, all local changes will be undone.
            self._run_command("git reset --hard", cwd=self.path)
        else:
            # If the commit hash is not the HEAD commit, revert to the specified commit and create a new revert commit.
            self._run_command(f"git revert --no-commit {commit_hash}..HEAD", cwd=self.path)
            self._run_command(
                f'git commit -m "reverting to {commit_hash}" --allow-empty', cwd=self.path
            )

    def is_git(self) -> bool:
        """Check if the directory is a git repository.

        Returns:
            bool: True if it's a git repository, False otherwise.
        """
        return Path(self.path).joinpath(".git").exists()

    def set_author(self, author):
        # TODO: maybe ask user to specify their own choices
        self._run_command(f'git config user.name "{author}"', cwd=self.path)
        self._run_command('git config user.email "sample@mail.com"', cwd=self.path)

    def clone(self, origin: str, force=False):
        """Clones the repository

        Args:
            origin (str): the remote
            force (bool, optional): states if the operation should be forced. Defaults to False.
        """
        self.init(force=force)
        self.set_remote(origin=origin)
        self.pull(origin=origin, force=force)

    def delete_repo_contents(self, include_git=False):
        """Deletes the contents of the git service

        Args:
            include_git (bool, optional): states if the .git directory should also be deleted. Defaults to False.
        """
        for root, dirs, files in os.walk(self.path):
            for f in files:
                os.unlink(os.path.join(root, f))
                self.log.info(f"Deleted {os.path.join(root, f)} from {self.git_root_dir}")
            for d in dirs:
                if d != ".git" or include_git:
                    shutil.rmtree(os.path.join(root, d))
                    self.log.info(f"Deleted {os.path.join(root, d)} from {self.git_root_dir}")

    # Note: dirs_exist_ok was only added in Python 3.8
    def copy_repo_contents(self, src: str, selected_files: List[str] = None):
        """copies repo contents from src to the git path

        Args:
            src (str): path where the to be copied files reside
            selected_files (List[str], optional): list of files to copy. Defaults to None.
        """
        ignore = shutil.ignore_patterns(".git", "__pycache__")
        if selected_files:
            self.log.info(f"Copying only selected files from {src} to {self.path}")
            for item in os.listdir(src):
                if item in selected_files:
                    s = os.path.join(src, item)
                    d = os.path.join(self.path, item)
                    if os.path.isdir(s):
                        shutil.copytree(s, d, ignore=ignore)
                    else:
                        shutil.copy2(s, d)
        else:
            self.log.info(f"Copying repository contents from {src} to {self.path}")
            shutil.copytree(src, self.path, ignore=ignore, dirs_exist_ok=True)

    def check_remote_status(self, origin: str, branch: str) -> RemoteFileStatus:
        untracked, added, modified, deleted = self.git_status(hidden_files=False)
        local_changes = any([untracked, added, modified, deleted])

        if self.local_branch_exists(branch):
            local = self._run_command(f"git rev-parse {branch}", cwd=self.path).strip()
        else:
            local = None
        if self.remote_branch_exists(origin, branch):
            remote = self._run_command(f"git rev-parse {origin}/{branch}", cwd=self.path).strip()
        else:
            return RemoteFileStatus.NO_REMOTE_REPO

        if local is None and remote:
            if local_changes:
                return RemoteFileStatus.DIVERGENT
            return RemoteFileStatus.PULL_NEEDED

        if local == remote:
            if local_changes:
                return RemoteFileStatus.PUSH_NEEDED
            return RemoteFileStatus.UP_TO_DATE

        base = self._run_command(
            f"git merge-base {branch} {origin}/{branch}", cwd=self.path
        ).strip()

        if local == base:
            return RemoteFileStatus.PULL_NEEDED
        elif remote == base:
            return RemoteFileStatus.PUSH_NEEDED
        else:
            return RemoteFileStatus.DIVERGENT

    def git_status(
        self, hidden_files: bool = False
    ) -> Tuple[List[str], List[str], List[str], List[str]]:
        files = self._run_command("git status --porcelain", cwd=self.path)
        untracked, added, modified, deleted = [], [], [], []
        for line in files.splitlines():
            k, v = line.split(maxsplit=1)
            if v[0] == "." and not hidden_files:  # TODO: implement nested check for hidden files
                continue
            if k == "??":
                untracked.append(v)
            elif k == "A":
                added.append(v)
            elif k == "M":
                modified.append(v)
            elif k == "D":
                deleted.append(v)
        return untracked, added, modified, deleted

    def check_remote_file_status(self, file_path: str) -> RemoteFileStatus:
        file_status_list = self._run_command(
            f"git status --porcelain {file_path}", cwd=self.path
        ).split(maxsplit=1)
        # Extract the status character from the list
        if file_status_list:
            file_status = file_status_list[0]
        else:
            # If the list is empty, the file is up-to-date
            return RemoteFileStatus.UP_TO_DATE
        # Convert the file status to the corresponding enum value
        if file_status in {"??", "M", "A", "D"}:
            return RemoteFileStatus.PUSH_NEEDED
        else:
            return RemoteFileStatus.DIVERGENT

    def local_branch_exists(self, branch: str) -> bool:
        try:
            self._run_command(f"git rev-parse --quiet --verify {branch}", cwd=self.path)
        except GitError:
            return False
        return True

    def remote_branch_exists(self, origin: str, branch: str) -> bool:
        try:
            self._run_command(f"git ls-remote --exit-code {origin} {branch}", cwd=self.path)
        except GitError:
            return False
        return True

    def get_log(self, history_count: int = 10) -> List[Dict[str, str]]:
        """
        Execute git log command & return the result.
        """
        cmd = f"git log --pretty=format:%H%n%an%n%at%n%D%n%s -{history_count}"
        my_output = self._run_command(cmd, cwd=self.path)

        result = []
        line_array = my_output.splitlines()
        previous_commit_offset = 5
        self.log.info(f"Found {len(line_array) // previous_commit_offset} commits in history")

        for i in range(0, len(line_array), previous_commit_offset):
            commit = {
                "commit": line_array[i],
                "author": line_array[i + 1],
                "date": datetime.fromtimestamp(int(line_array[i + 2])).isoformat(
                    "T", "milliseconds"
                )
                + "Z",
                # "date": line_array[i + 2],
                "ref": line_array[i + 3],
                "commit_msg": line_array[i + 4],
                "pre_commit": "",
            }

            if i + previous_commit_offset < len(line_array):
                commit["pre_commit"] = line_array[i + previous_commit_offset]

            result.append(commit)

        return result

    @property
    def git_version(self):
        """Return the git version

        Returns:
            tuple: the git version
        """
        if self._git_version is None:
            try:
                version = self._run_command("git --version", cwd=self.path)
            except GitError:
                return tuple()
            version = version.split(" ")[2]
            self._git_version = tuple([int(v) for v in version.split(".")])
        return self._git_version

    def commit(self, message: str = str(datetime.now()), selected_files: List[str] = None):
        """Commit staged changes.

        Args:
            message (str): The commit message. Defaults to the current datetime.
            selected_files (List[str]): Specific files to commit. Defaults to None.
        """
        if selected_files:
            for file in selected_files:
                self._run_command(f"git add {shlex.quote(file)}", cwd=self.path)
        else:
            self._run_command("git add .", cwd=self.path)

        self.log.info(f"Committing changes with message: {message}")
        self._run_command(f'git commit --allow-empty -m "{message}"', cwd=self.path)

    def _run_command(self, command: str, cwd: str) -> Union[str, None]:
        """Run a shell command and return the output.

        Args:
            command (str): The command to run.
            cwd (str): The working directory for the command.
        """

        self.log.debug(f"Executing command: {command} in {cwd}")
        try:
            result = subprocess.run(
                command, shell=True, check=True, cwd=cwd, text=True, capture_output=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            self.log.error(f"Command failed with error: {e.stderr}")
            raise GitError(code=e.returncode, error=e.stderr)
