# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import json
import os
import shutil
from http import HTTPStatus
from typing import List, Optional
from urllib.parse import quote, unquote

from grader_service.convert.converters.base import GraderConvertException
from grader_service.convert.converters.generate_assignment import GenerateAssignment
from grader_service.errors import APIError
from grader_service.handlers import GitRepoType
from tornado.web import HTTPError, authenticated

from grader_labextension.api.models.assignment_settings import AssignmentSettings
from grader_labextension.services.request import RequestServiceError

from ..api.models.submission import Submission
from ..registry import register_handler
from ..services.git import GitError, GitService
from .base_handler import ExtensionBaseHandler


@register_handler(
    path=r"api\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/generate\/?"
)
class GenerateHandler(ExtensionBaseHandler):
    """
    Tornado Handler class for http requests to
    /lectures/{lecture_id}/assignments/{assignment_id}/generate.
    """

    async def put(self, lecture_id: int, assignment_id: int):
        """Generates the release files from the source files of an assignment

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        """
        lecture = await self.get_lecture(lecture_id)
        code = lecture["code"]

        output_dir = f"{self.root_dir}/{code}/release/{assignment_id}"
        os.makedirs(os.path.expanduser(output_dir), exist_ok=True)

        generator = GenerateAssignment(
            input_dir=f"{self.root_dir}/{code}/source/{assignment_id}",
            output_dir=output_dir,
            file_pattern="*.ipynb",
            assignment_settings=AssignmentSettings(allowed_files=["*"]),
        )
        generator.force = True
        generator.log = self.log

        try:
            # delete contents of output directory since we might have chosen to disallow files
            self.log.info("Deleting files in release directory")
            shutil.rmtree(output_dir)
            os.mkdir(output_dir)
        except Exception as e:
            self.log.error(e)
            raise APIError(HTTPStatus.INTERNAL_SERVER_ERROR, message=str(e))

        self.log.info("Starting GenerateAssignment converter")
        try:
            generator.start()
        except Exception as e:
            self.log.error(e)
            raise APIError(HTTPStatus.CONFLICT, message=str(e))

        gradebook_path = os.path.join(generator._output_directory, "gradebook.json")
        try:
            os.remove(gradebook_path)
            self.log.info(f"Successfully deleted {gradebook_path}")
        except OSError as e:
            self.log.error(f"Could not delete {gradebook_path}! Error: {e.strerror}")
        self.log.info("GenerateAssignment conversion done")
        self.write({"status": "OK"})


@register_handler(
    path=r"api\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/"
    r"remote-file-status\/(?P<repo>\w*)\/?"
)
class GitRemoteFileStatusHandler(ExtensionBaseHandler):
    """
    Tornado Handler class for http requests to
    /lectures/{lecture_id}/assignments/{assignment_id}/remote-file-status/{repo}.
    """

    @authenticated
    async def get(self, lecture_id: int, assignment_id: int, repo: str):
        if repo not in {GitRepoType.USER, GitRepoType.SOURCE, GitRepoType.RELEASE}:
            self.log.error(HTTPStatus.NOT_FOUND)
            raise HTTPError(HTTPStatus.NOT_FOUND, reason=f"Repository {repo} does not exist")

        lecture = await self.get_lecture(lecture_id)
        assignment = await self.get_assignment(lecture_id, assignment_id)
        file_path = self.get_query_argument("file")
        git_service = GitService(
            server_root_dir=self.root_dir,
            lecture_code=lecture["code"],
            assignment_id=assignment["id"],
            repo_type=GitRepoType(repo),
            config=self.config,
            force_user_repo=repo == GitRepoType.RELEASE,
        )
        try:
            if not git_service.is_git():
                git_service.init()
                git_service.set_author(author=self.user_name)
            git_service.set_remote(f"grader_{repo}")
            git_service.fetch_all()
            status = git_service.check_remote_file_status(file_path)
            self.log.info(f"File {file_path} status: {status}")
        except GitError as e:
            self.log.error(e)
            raise APIError(502, message=e.error)
        response = json.dumps({"status": status.name})
        self.write(response)


@register_handler(
    path=r"api\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/"
    r"remote-status\/(?P<repo>\w*)\/?"
)
class GitRemoteStatusHandler(ExtensionBaseHandler):
    """
    Tornado Handler class for http requests to
    /lectures/{lecture_id}/assignments/{assignment_id}/remote_status/{repo}.
    """

    @authenticated
    async def get(self, lecture_id: int, assignment_id: int, repo: str):
        if repo not in {GitRepoType.USER, GitRepoType.SOURCE, GitRepoType.RELEASE}:
            self.log.error(HTTPStatus.NOT_FOUND)
            raise HTTPError(HTTPStatus.NOT_FOUND, reason=f"Repository {repo} does not exist")

        lecture = await self.get_lecture(lecture_id)
        assignment = await self.get_assignment(lecture_id, assignment_id)

        git_service = GitService(
            server_root_dir=self.root_dir,
            lecture_code=lecture["code"],
            assignment_id=assignment["id"],
            repo_type=GitRepoType(repo),
            config=self.config,
            force_user_repo=repo == GitRepoType.RELEASE,
        )
        try:
            if not git_service.is_git():
                git_service.init()
                git_service.set_author(author=self.user_name)
            git_service.set_remote(f"grader_{repo}")
            git_service.fetch_all()
            status = git_service.check_remote_status(f"grader_{repo}", "main")
        except GitError as e:
            self.log.error(e)
            raise APIError(502, reason="error fetching remote files", message=e.error)
        response = json.dumps({"status": status.name})
        self.write(response)


@register_handler(
    path=r"api\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/log\/"
    r"(?P<repo>\w*)\/?"
)
class GitLogHandler(ExtensionBaseHandler):
    """
    Tornado Handler class for http requests to
    /lectures/{lecture_id}/assignments/{assignment_id}/log/{repo}.
    """

    @authenticated
    async def get(self, lecture_id: int, assignment_id: int, repo: str):
        """
        Sends a GET request to the grader service to get the logs of a given repo.

        :param lecture_id: id of the lecture
        :param assignment_id: id of the assignment
        :param repo: repo name
        :return: logs of git repo
        """
        if repo not in {GitRepoType.USER, GitRepoType.SOURCE, GitRepoType.RELEASE}:
            self.log.error(HTTPStatus.NOT_FOUND)
            raise HTTPError(HTTPStatus.NOT_FOUND, reason=f"Repository {repo} does not exist")
        n_history = int(self.get_argument("n", "10"))

        lecture = await self.get_lecture(lecture_id)
        assignment = await self.get_assignment(lecture_id, assignment_id)

        git_service = GitService(
            server_root_dir=self.root_dir,
            lecture_code=lecture["code"],
            assignment_id=assignment["id"],
            repo_type=GitRepoType(repo),
            config=self.config,
            force_user_repo=repo == GitRepoType.RELEASE,
        )
        try:
            if not git_service.is_git():
                git_service.init()
                git_service.set_author(author=self.user_name)
            git_service.set_remote(f"grader_{repo}")
            git_service.fetch_all()
            if git_service.local_branch_exists("main"):  # at least main should exist
                logs = git_service.get_log(n_history)
            else:
                logs = []
        except GitError as e:
            self.log.error(e)
            raise APIError(502, message=e.error)

        self.write(json.dumps(logs))


@register_handler(
    path=r"api\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/pull\/"
    r"(?P<repo>\w*)\/?"
)
class PullHandler(ExtensionBaseHandler):
    """
    Tornado Handler class for http requests to
    /lectures/{lecture_id}/assignments/{assignment_id}/pull/{repo}.
    """

    @authenticated
    async def get(self, lecture_id: int, assignment_id: int, repo: str):
        """Creates a local repository and pulls the specified repo type

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        :param repo: type of the repository
        :type repo: str
        """
        if repo not in {
            GitRepoType.USER,
            GitRepoType.SOURCE,
            GitRepoType.RELEASE,
            GitRepoType.EDIT,
            GitRepoType.FEEDBACK,
        }:
            self.log.error(HTTPStatus.NOT_FOUND)
            raise HTTPError(HTTPStatus.NOT_FOUND, reason=f"Repository {repo} does not exist")

        # Submission id needed for edit repository
        sub_id = self.get_argument("subid", None)

        lecture = await self.get_lecture(lecture_id)
        assignment = await self.get_assignment(lecture_id, assignment_id)

        git_service = GitService(
            server_root_dir=self.root_dir,
            lecture_code=lecture["code"],
            assignment_id=assignment["id"],
            repo_type=GitRepoType(repo),
            config=self.config,
            force_user_repo=repo == GitRepoType.RELEASE,
            sub_id=sub_id if sub_id is None else int(sub_id),
            log=self.log,
        )
        try:
            if not git_service.is_git():
                git_service.init()
                git_service.set_author(author=self.user_name)
            git_service.set_remote(
                f"grader_{repo}", additional_path=sub_id if sub_id is not None else ""
            )
            git_service.pull(f"grader_{repo}", force=True)
            self.write({"status": "OK"})
        except GitError as e:
            self.log.error("Git error:\n" + e.error)
            raise APIError(502, message=e.error)


@register_handler(
    path=r"api\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/push\/"
    r"(?P<repo>\w*)\/?"
)
class PushHandler(ExtensionBaseHandler):
    """
    Tornado Handler class for http requests to
    /lectures/{lecture_id}/assignments/{assignment_id}/push/{repo}.
    """

    async def put(self, lecture_id: int, assignment_id: int, repo: str):
        """Pushes from the local repositories to remote

        If the repo type is release, it also generates the release files and updates the assignment
        properties in the grader service

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        :param repo: type of the repository
        :type repo: str
        """
        if repo not in {
            GitRepoType.USER,
            GitRepoType.SOURCE,
            GitRepoType.RELEASE,
            GitRepoType.EDIT,
        }:
            self.write_error(404)

        # Extract request parameters
        sub_id, commit_message, selected_files, submit, username = self._extract_request_params()

        # Validate commit message for 'source' repo
        if repo == GitRepoType.SOURCE:
            self._validate_commit_message(commit_message)

        # Fetch lecture and assignment data
        lecture = await self.get_lecture(lecture_id)
        assignment = await self.get_assignment(lecture_id, assignment_id)

        if repo == GitRepoType.EDIT and sub_id is None:
            # Create a new submission for the student `username`
            sub_id = await self._create_submission_for_user(lecture_id, assignment_id, username)

        # Initialize GitService
        git_service = GitService(
            server_root_dir=self.root_dir,
            lecture_code=lecture["code"],
            assignment_id=assignment["id"],
            repo_type=GitRepoType(repo),
            config=self.config,
            sub_id=sub_id,
            username=username,
        )

        # Handle 'release' repo
        if repo == GitRepoType.RELEASE:
            await self._handle_release_repo(
                git_service, lecture, assignment, lecture_id, assignment_id, selected_files
            )

        # Commit and push the files
        await self._perform_git_operations(
            git_service, repo, commit_message, selected_files, sub_id
        )

        # Handle submission for 'user' (formerly: 'assignment') repo
        if submit and repo == GitRepoType.USER:
            await self._submit_assignment(git_service, lecture_id, assignment_id)

        self.write({"status": "OK"})

    def _extract_request_params(
        self,
    ) -> tuple[Optional[str], Optional[str], List[str], bool, Optional[str]]:
        sub_id_str = self.get_argument("subid", None)
        commit_message = self.get_argument("commit-message", None)
        selected_files = self.get_arguments("selected-files")
        submit = self.get_argument("submit", "false") == "true"
        username = self.get_argument("for_user", None)
        try:
            sub_id = int(sub_id_str)
        except (TypeError, ValueError):
            sub_id = None
        return sub_id, commit_message, selected_files, submit, username

    def _validate_commit_message(self, commit_message):
        if not commit_message:
            self.log.error("Commit message was not found")
            raise HTTPError(HTTPStatus.NOT_FOUND, reason="Commit message was not found")

    async def _create_submission_for_user(
        self, lecture_id: int, assignment_id: int, username: Optional[str]
    ) -> int:
        """Creates a new submission for the user `username`."""
        if username is None:
            self.log.error("Username has to be provided when creating a submission")
            raise HTTPError(HTTPStatus.BAD_REQUEST, reason="Missing 'for_user' value in request")
        response = None
        try:
            response = await self.request_service.request(
                "POST",
                f"{self.service_base_url}api/lectures/{lecture_id}/assignments/{assignment_id}/"
                f"submissions",
                body={"commit_hash": "0" * 40, "username": username},
                header=self.grader_authentication_header,
            )
        except RequestServiceError as e:
            self.log.error(f"Error creating submission for user {username}")
            raise HTTPError(e.code, reason=e.message)
        submission = Submission.from_dict(response)
        submission.submitted_at = response["submitted_at"]
        submission.edited = True

        self.log.info(
            "Created submission %s for user %s and pushing to edit repo...", submission.id, username
        )
        try:
            await self.request_service.request(
                "PUT",
                f"{self.service_base_url}api/lectures/{lecture_id}/assignments/{assignment_id}/"
                f"submissions/{submission.id}",
                body=submission.to_dict(),
                header=self.grader_authentication_header,
            )
        except RequestServiceError as e:
            self.log.error(f"Error updating submission {submission.id}")
            raise HTTPError(e.code, reason=e.message)
        return submission.id

    async def _handle_release_repo(
        self, git_service, lecture, assignment, lecture_id, assignment_id, selected_files
    ):
        git_service.delete_repo_contents(include_git=True)
        src_path = GitService(
            self.root_dir,
            lecture["code"],
            assignment["id"],
            repo_type=GitRepoType.SOURCE,
            config=self.config,
        ).path

        if selected_files:
            self.log.info(f"Selected files to push to release repo: {selected_files}")

        git_service.copy_repo_contents(src=src_path, selected_files=selected_files)

        generator = self._initialize_generator(src_path, git_service.path)
        await self._generate_release_files(generator, git_service.path)

        gradebook_path = os.path.join(git_service.path, "gradebook.json")
        await self._update_assignment_properties(gradebook_path, lecture_id, assignment_id)

        try:
            os.remove(gradebook_path)
            self.log.info(f"Successfully deleted {gradebook_path}")
        except OSError as e:
            self.log.error(f"Cannot delete {gradebook_path}! Error: {e.strerror}\nAborting push!")
            raise HTTPError(
                HTTPStatus.CONFLICT,
                reason=f"Cannot delete {gradebook_path}! Error: {e.strerror}\nAborting push!",
            )

    def _initialize_generator(self, src_path, output_path):
        generator = GenerateAssignment(
            input_dir=src_path,
            output_dir=output_path,
            file_pattern="*.ipynb",
            assignment_settings=AssignmentSettings(allowed_files=["*"]),
        )
        generator.force = True
        generator.log = self.log
        return generator

    async def _generate_release_files(self, generator, output_path):
        try:
            shutil.rmtree(output_path)
            os.mkdir(output_path)
        except Exception as e:
            self.log.error(e)
            raise APIError(HTTPStatus.INTERNAL_SERVER_ERROR, message=str(e))

        self.log.info("Starting GenerateAssignment converter")
        try:
            generator.start()
            self.log.info("GenerateAssignment conversion done")
        except GraderConvertException as e:
            self.log.error("Converting failed: Error converting notebook!", exc_info=True)
            raise APIError(HTTPStatus.CONFLICT, message=str(e))

    async def _update_assignment_properties(self, gradebook_path, lecture_id, assignment_id):
        try:
            with open(gradebook_path, "r") as f:
                gradebook_json = json.load(f)

            try:
                # update assignment properties in grader service with the generated gradebook.json
                await self.request_service.request(
                    "PUT",
                    f"{self.service_base_url}api/lectures/{lecture_id}/assignments/{assignment_id}/"
                    f"properties",
                    header=self.grader_authentication_header,
                    body=gradebook_json,
                    decode_response=False,
                )
            except RequestServiceError as e:
                self.log.error(e)
                raise APIError(e.code, message=e.message)
        except FileNotFoundError:
            self.log.error(f"Cannot find gradebook file: {gradebook_path}")
            raise HTTPError(
                HTTPStatus.NOT_FOUND, reason=f"Cannot find gradebook file: {gradebook_path}"
            )

    async def _perform_git_operations(
        self,
        git_service: GitService,
        repo: GitRepoType,
        commit_message: str,
        selected_files,
        sub_id: Optional[int] = None,
    ):
        remote = f"grader_{repo}"
        try:
            if not git_service.is_git():
                git_service.init()
                git_service.set_author(author=self.user_name)
            git_service.set_remote(
                remote, additional_path=str(sub_id) if sub_id is not None else ""
            )
        except GitError as e:
            self.log.error("git error during git initiation process: %s", e.error)
            raise APIError(502, message=e.error)

        try:
            git_service.commit(message=commit_message, selected_files=selected_files)
        except GitError as e:
            self.log.error("git error during commit process: %s", e.error)
            raise APIError(502, reason="git commit failed", message=e.error)
        try:
            git_service.push(remote, force=True)
        except GitError as e:
            self.log.error("git error during push process: %s", e.error)
            git_service.undo_commit()
            raise APIError(502, reason="git push failed", message=e.error)

    async def _submit_assignment(self, git_service, lecture_id, assignment_id):
        self.log.info(f"Submitting assignment {assignment_id}!")
        try:
            latest_commit_hash = git_service.get_log(history_count=1)[0]["commit"]
        except (KeyError, IndexError) as e:
            self.log.error(e)
            raise APIError(HTTPStatus.INTERNAL_SERVER_ERROR, message=str(e))

        try:
            response = await self.request_service.request(
                "POST",
                f"{self.service_base_url}api/lectures/{lecture_id}/assignments/{assignment_id}/"
                f"submissions",
                body={"commit_hash": latest_commit_hash},
                header=self.grader_authentication_header,
            )
        except RequestServiceError as e:
            self.log.error(e)
            raise APIError(e.code, message=e.message)

        self.write(json.dumps(response))


@register_handler(
    path=r"api\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/reset\/?"
)
class ResetHandler(ExtensionBaseHandler):
    """
    Tornado Handler class for http requests to /lectures/{lecture_id}/assignments/{assignment_id}/reset.
    """

    @authenticated
    async def get(self, lecture_id: int, assignment_id: int):
        """
        Sends a GET request to the grader service that resets the user repo.

        :param lecture_id: id of the lecture
        :param assignment_id: id of the assignment
        :return: void
        """
        try:
            await self.request_service.request(
                "GET",
                f"{self.service_base_url}api/lectures/{lecture_id}/assignments/{assignment_id}/"
                f"reset",
                header=self.grader_authentication_header,
            )
        except RequestServiceError as e:
            self.log.error(e)
            raise APIError(e.code, message=e.message)
        self.write({"status": "OK"})


@register_handler(
    path=r"api\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/restore\/"
    r"(?P<commit_hash>\w*)\/?"
)
class RestoreHandler(ExtensionBaseHandler):
    @authenticated
    async def get(self, lecture_id: int, assignment_id: int, commit_hash: str):
        lecture = await self.get_lecture(lecture_id)
        assignment = await self.get_assignment(lecture_id, assignment_id)

        git_service = GitService(
            server_root_dir=self.root_dir,
            lecture_code=lecture["code"],
            assignment_id=assignment["id"],
            repo_type=GitRepoType.USER,
            config=self.config,
            force_user_repo=False,
            sub_id=None,
        )
        try:
            if not git_service.is_git():
                git_service.init()
                git_service.set_author(author=self.user_name)
            git_service.set_remote(f"grader_{GitRepoType.USER}")
            # first reset by pull so there are no changes in the repository before reverting
            git_service.pull(f"grader_{GitRepoType.USER}", force=True)
            git_service.revert(commit_hash=commit_hash)
            git_service.push(f"grader_{GitRepoType.USER}")
            self.write({"status": "OK"})
        except GitError as e:
            self.log.error("Git error:\n" + e.error)
            raise APIError(502, message=e.error)


@register_handler(path=r"\/(?P<lecture_id>\d*)\/(?P<assignment_id>\d*)\/(?P<notebook_name>.*)")
class NotebookAccessHandler(ExtensionBaseHandler):
    """
    Tornado Handler class for http requests to
    /lectures/{lecture_id}/assignments/{assignment_id}/{notebook_name}.
    """

    @authenticated
    async def get(self, lecture_id: int, assignment_id: int, notebook_name: str):
        """
        Sends a GET request to the grader service to access notebook and redirect to it.
        :param lecture_id: id of the lecture
        :param assignment_id: id of the assignment
        :param notebook_name: notebook name
        :return: void
        """
        notebook_name = unquote(notebook_name)

        try:
            lecture = await self.get_lecture(lecture_id)
            assignment = await self.get_assignment(lecture_id, assignment_id)
        except RequestServiceError as e:
            self.set_status(e.code)
            self.write_error(e.code)
            return

        git_service = GitService(
            server_root_dir=self.root_dir,
            lecture_code=lecture["code"],
            assignment_id=assignment["id"],
            repo_type=GitRepoType.RELEASE,
            config=self.config,
            force_user_repo=True,
        )

        if not git_service.is_git():
            try:
                git_service.init()
                git_service.set_author(author=self.user_name)
                git_service.set_remote(f"grader_{GitRepoType.RELEASE}")
                git_service.pull(f"grader_{GitRepoType.RELEASE}", force=True)
                self.write({"status": "OK"})
            except GitError as e:
                self.log.error("Git error:\n" + e.error)
                raise APIError(502, message=e.error)

        try:
            username = self.current_user["name"]
        except TypeError as e:
            self.log.error(e)
            raise APIError(HTTPStatus.INTERNAL_SERVER_ERROR, message=str(e))

        url = (
            f"/user/{username}/lab/tree/{lecture['code']}/{assignment['id']}/{quote(notebook_name)}"
        )
        self.log.info(f"Redirecting to {url}")
        self.redirect(url)
