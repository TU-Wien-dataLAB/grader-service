# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import json
import os
import shutil
from http import HTTPStatus
from urllib.parse import unquote, quote
from tornado.web import HTTPError

from grader_convert.converters.base import GraderConvertException
from grader_convert.converters.generate_assignment import GenerateAssignment
from .base_handler import ExtensionBaseHandler, cache
from ..api.models.submission import Submission
from ..registry import register_handler
from ..services.git import GitError, GitService
from tornado.httpclient import HTTPClientError, HTTPResponse


@register_handler(
    path=r"\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/generate\/?"
)
class GenerateHandler(ExtensionBaseHandler):
    """
    Tornado Handler class for http requests to /lectures/{lecture_id}/assignments/{assignment_id}/generate.
    """

    async def put(self, lecture_id: int, assignment_id: int):
        """Generates the release files from the source files of a assignment

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        """
        try:
            lecture = await self.request_service.request(
                "GET",
                f"{self.service_base_url}/lectures/{lecture_id}",
                header=self.grader_authentication_header,
            )
            assignment = await self.request_service.request(
                "GET",
                f"{self.service_base_url}/lectures/{lecture_id}/assignments/{assignment_id}",
                header=self.grader_authentication_header,
            )
        except HTTPClientError as e:
            self.log.error(e.response)
            raise HTTPError(e.code, reason=e.response.reason)
        code = lecture["code"]
        a_id = assignment["id"]

        output_dir = f"{self.root_dir}/release/{code}/{a_id}"
        os.makedirs(
            os.path.expanduser(output_dir),
            exist_ok=True,
        )

        generator = GenerateAssignment(
            input_dir=f"{self.root_dir}/source/{code}/{a_id}",
            output_dir=output_dir,
            file_pattern="*.ipynb",
            copy_files=True  # Always copy files from source to release
        )
        generator.force = True

        try:
            # delete contents of output directory since we might have chosen to disallow files
            self.log.info("Deleting files in release directory")
            shutil.rmtree(output_dir)
            os.mkdir(output_dir)
        except Exception as e:
            self.log.error(e)
            raise HTTPError(HTTPStatus.INTERNAL_SERVER_ERROR, reason=str(e))

        self.log.info("Starting GenerateAssignment converter")
        try:
            generator.start()
        except Exception as e:
            self.log.error(e)
            raise HTTPError(HTTPStatus.CONFLICT, reason=str(e))
        try:
            gradebook_path = os.path.join(generator._output_directory, "gradebook.json")
            os.remove(gradebook_path)
            self.log.info(f"Successfully deleted {gradebook_path}")
        except OSError as e:
            self.log.error(f"Could delete {gradebook_path}! Error: {e.strerror}")
        self.log.info("GenerateAssignment conversion done")
        self.write("OK")


@register_handler(
    path=r"\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/remote-status\/(?P<repo>\w*)\/?"
)
class GitRemoteStatusHandler(ExtensionBaseHandler):
    """
    Tornado Handler class for http requests to /lectures/{lecture_id}/assignments/{assignment_id}/remote_status/{repo}.
    """

    @cache(max_age=15)
    async def get(self, lecture_id: int, assignment_id: int, repo: str):
        if repo not in {"assignment", "source", "release"}:
            self.log.error(HTTPStatus.NOT_FOUND)
            raise HTTPError(HTTPStatus.NOT_FOUND, reason=f"Repository {repo} does not exist")
        lecture = await self.get_lecture(lecture_id)
        assignment = await self.get_assignment(lecture_id, assignment_id)
        git_service = GitService(
            server_root_dir=self.root_dir,
            lecture_code=lecture["code"],
            assignment_id=assignment["id"],
            repo_type=repo,
            config=self.config,
            force_user_repo=True if repo == "release" else False,
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
            raise HTTPError(HTTPStatus.INTERNAL_SERVER_ERROR, reason=e)
        self.write(status.name)


@register_handler(
    path=r"\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/log\/(?P<repo>\w*)\/?"
)
class GitLogHandler(ExtensionBaseHandler):
    """
    Tornado Handler class for http requests to /lectures/{lecture_id}/assignments/{assignment_id}/log/{repo}.
    """

    @cache(max_age=15)
    async def get(self, lecture_id: int, assignment_id: int, repo: str):
        """
        Sends a GET request to the grader service to get the logs of a given repo.

        :param lecture_id: id of the lecture
        :param assignment_id: id of the assignment
        :param repo: repo name
        :return: logs of git repo
        """
        if repo not in {"assignment", "source", "release"}:
            self.log.error(HTTPStatus.NOT_FOUND)
            raise HTTPError(HTTPStatus.NOT_FOUND, reason=f"Repository {repo} does not exist")
        n_history = int(self.get_argument("n", "10"))
        try:
            lecture = await self.request_service.request(
                "GET",
                f"{self.service_base_url}/lectures/{lecture_id}",
                header=self.grader_authentication_header,
            )
            assignment = await self.request_service.request(
                "GET",
                f"{self.service_base_url}/lectures/{lecture_id}/assignments/{assignment_id}",
                header=self.grader_authentication_header,
            )
        except HTTPClientError as e:
            self.log.error(e.response)
            raise HTTPError(e.code, reason=e.response.reason)

        git_service = GitService(
            server_root_dir=self.root_dir,
            lecture_code=lecture["code"],
            assignment_id=assignment["id"],
            repo_type=repo,
            config=self.config,
            force_user_repo=True if repo == "release" else False,
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
            raise HTTPError(HTTPStatus.INTERNAL_SERVER_ERROR, reason=e)

        self.write(json.dumps(logs))


@register_handler(
    path=r"\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/pull\/(?P<repo>\w*)\/?"
)
class PullHandler(ExtensionBaseHandler):
    """
    Tornado Handler class for http requests to /lectures/{lecture_id}/assignments/{assignment_id}/pull/{repo}.
    """

    async def get(self, lecture_id: int, assignment_id: int, repo: str):
        """Creates a local repository and pulls the specified repo type

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        :param repo: type of the repository
        :type repo: str
        """
        if repo not in {"assignment", "source", "release"}:
            self.log.error(HTTPStatus.NOT_FOUND)
            raise HTTPError(HTTPStatus.NOT_FOUND, reason=f"Repository {repo} does not exist")
        try:
            lecture = await self.request_service.request(
                "GET",
                f"{self.service_base_url}/lectures/{lecture_id}",
                header=self.grader_authentication_header,
            )
            assignment = await self.request_service.request(
                "GET",
                f"{self.service_base_url}/lectures/{lecture_id}/assignments/{assignment_id}",
                header=self.grader_authentication_header,
            )
        except HTTPClientError as e:
            self.log.error(e.response)
            raise HTTPError(e.code, reason=e.response.reason)

        git_service = GitService(
            server_root_dir=self.root_dir,
            lecture_code=lecture["code"],
            assignment_id=assignment["id"],
            repo_type=repo,
            config=self.config,
            force_user_repo=repo == "release",
        )
        try:
            if not git_service.is_git():
                git_service.init()
                git_service.set_author(author=self.user_name)
            git_service.set_remote(f"grader_{repo}")
            git_service.pull(f"grader_{repo}", force=True)
            self.write("OK")
        except GitError as e:
            self.log.error("GitError:\n" + e.error)
            raise HTTPError(HTTPStatus.INTERNAL_SERVER_ERROR, reason=e.error)


@register_handler(
    path=r"\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/push\/(?P<repo>\w*)\/?"
)
class PushHandler(ExtensionBaseHandler):
    """
    Tornado Handler class for http requests to /lectures/{lecture_id}/assignments/{assignment_id}/push/{repo}.
    """

    async def put(self, lecture_id: int, assignment_id: int, repo: str):
        """Pushes from the local repositories to remote
            If the repo type is release, it also generate the release files and updates the assignment properties in the grader service

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        :param repo: type of the repository
        :type repo: str
        """
        if repo not in {"assignment", "source", "release"}:
            self.write_error(404)
        commit_message = self.get_argument("commit-message", None)
        submit = self.get_argument("submit", "false") == "true"
        if repo == "source" and (commit_message is None or commit_message == ""):
            self.log.error("Commit message was not found")
            raise HTTPError(HTTPStatus.NOT_FOUND, reason="Commit message was not found")

        try:
            lecture = await self.request_service.request(
                "GET",
                f"{self.service_base_url}/lectures/{lecture_id}",
                header=self.grader_authentication_header,
            )
            assignment = await self.request_service.request(
                "GET",
                f"{self.service_base_url}/lectures/{lecture_id}/assignments/{assignment_id}",
                header=self.grader_authentication_header,
            )
        except HTTPClientError as e:
            self.log.error(e.response)
            raise HTTPError(e.code, reason=e.response.reason)

        git_service = GitService(
            server_root_dir=self.root_dir,
            lecture_code=lecture["code"],
            assignment_id=assignment["id"],
            repo_type=repo,
            config=self.config,
        )

        if repo == "release":
            git_service.delete_repo_contents(include_git=True)
            src_path = GitService(
                self.root_dir,
                lecture["code"],
                assignment["id"],
                repo_type="source",
                config=self.config,
            ).path
            git_service.copy_repo_contents(src=src_path)

            # call nbconvert before pushing
            generator = GenerateAssignment(
                input_dir=src_path,
                output_dir=git_service.path,
                file_pattern="*.ipynb",
                copy_files=True  # Always copy files from source to release
            )
            generator.force = True

            try:
                # delete contents of output directory since we might have chosen to disallow files
                self.log.info("Deleting files in release directory")
                shutil.rmtree(git_service.path)
                os.mkdir(git_service.path)
            except Exception as e:
                self.log.error(e)
                raise HTTPError(HTTPStatus.INTERNAL_SERVER_ERROR, reason=str(e))

            self.log.info("Starting GenerateAssignment converter")
            try:
                generator.start()
                self.log.info("GenerateAssignment conversion done")
            except GraderConvertException as e:
                self.log.error("Converting failed: Error converting notebook!", exc_info=True)

                raise HTTPError(409, reason=str(e))
            try:
                gradebook_path = os.path.join(git_service.path, "gradebook.json")
                self.log.info(f"Reading gradebook file: {gradebook_path}")
                with open(gradebook_path, "r") as f:
                    gradebook_json: dict = json.load(f)
            except FileNotFoundError:
                self.log.error(f"Cannot find gradebook file: {gradebook_path}")
                raise HTTPError(HTTPStatus.INTERNAL_SERVER_ERROR,
                                reason=f"Cannot find gradebook file: {gradebook_path}")

            self.log.info(f"Setting properties of assignment from {gradebook_path}")
            response: HTTPResponse = await self.request_service.request(
                "PUT",
                f"{self.service_base_url}/lectures/{lecture_id}/assignments/{assignment_id}/properties",
                header=self.grader_authentication_header,
                body=gradebook_json,
                decode_response=False,
            )
            if response.code == 200:
                self.log.info("Properties set for assignment")
            else:
                self.log.error(
                    f"Could not set assignment properties! Error code {response.code}"
                )

            try:
                os.remove(gradebook_path)
                self.log.info(f"Successfully deleted {gradebook_path}")
            except OSError as e:
                self.log.error(
                    f"Cannot delete {gradebook_path}! Error: {e.strerror}\nAborting push!"
                )
                raise HTTPError(HTTPStatus.INTERNAL_SERVER_ERROR,
                                reason=f"Cannot delete {gradebook_path}! Error: {e.strerror}\nAborting push!")

        self.log.info(f"File contents of {repo}: {git_service.path}")
        self.log.info(",".join(os.listdir(git_service.path)))

        try:
            if not git_service.is_git():
                git_service.init()
                git_service.set_author(author=self.user_name)
                # TODO: create .gitignore file
            git_service.set_remote(f"grader_{repo}")
        except GitError as e:
            self.log.error("GitError:\n" + e.error)
            raise HTTPError(HTTPStatus.INTERNAL_SERVER_ERROR, reason=e.error)

        try:
            git_service.commit(m=commit_message)
        except GitError as e:
            self.log.error("GitError:\n" + e.error)
            raise HTTPError(HTTPStatus.INTERNAL_SERVER_ERROR, reason=e.error)

        try:
            git_service.push(f"grader_{repo}", force=True)
        except GitError as e:
            self.log.error("GitError:\n" + e.error)
            raise HTTPError(HTTPStatus.INTERNAL_SERVER_ERROR, reason=str(e.error))

        if submit and repo == "assignment":
            self.log.info(f"Submitting assignment {assignment_id}!")
            try:
                latest_commit_hash = git_service.get_log(history_count=1)[0]["commit"]
                submission = Submission(commit_hash=latest_commit_hash)
                response = await self.request_service.request(
                    "POST",
                    f"{self.service_base_url}/lectures/{lecture_id}/assignments/{assignment_id}/submissions",
                    body=submission.to_dict(),
                    header=self.grader_authentication_header,
                )
                self.write(json.dumps(response))
                return
            except (KeyError, IndexError) as e:
                self.log.error(e)
                raise HTTPError(HTTPStatus.INTERNAL_SERVER_ERROR, reason=e)
            except HTTPClientError as e:
                self.log.error(e.response)
                raise HTTPError(e.code, reason=e.response.reason)

        self.write("OK")


@register_handler(
    path=r"\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/reset\/?"
)
class ResetHandler(ExtensionBaseHandler):
    """
    Tornado Handler class for http requests to /lectures/{lecture_id}/assignments/{assignment_id}/reset.
    """

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
                f"{self.service_base_url}/lectures/{lecture_id}/assignments/{assignment_id}/reset",
                header=self.grader_authentication_header,
            )
        except HTTPClientError as e:
            self.log.error(e.response)
            raise HTTPError(e.code, reason=e.response.reason)
        self.write("OK")


@register_handler(
    path=r"\/(?P<lecture_id>\d*)\/(?P<assignment_id>\d*)\/(?P<notebook_name>.*)"
)
class NotebookAccessHandler(ExtensionBaseHandler):
    """
    Tornado Handler class for http requests to /lectures/{lecture_id}/assignments/{assignment_id}/{notebook_name}.
    """

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
            lecture = await self.request_service.request(
                "GET",
                f"{self.service_base_url}/lectures/{lecture_id}",
                header=self.grader_authentication_header,
            )
            assignment = await self.request_service.request(
                "GET",
                f"{self.service_base_url}/lectures/{lecture_id}/assignments/{assignment_id}",
                header=self.grader_authentication_header,
            )
        except HTTPClientError as e:
            self.set_status(e.code)
            self.write_error(e.code)
            return

        git_service = GitService(
            server_root_dir=self.root_dir,
            lecture_code=lecture["code"],
            assignment_id=assignment["id"],
            repo_type="release",
            config=self.config,
            force_user_repo=True,
        )

        if not git_service.is_git():
            try:
                git_service.init()
                git_service.set_author(author=self.user_name)
                git_service.set_remote(f"grader_release")
                git_service.pull(f"grader_release", force=True)
                self.write("OK")
            except GitError as e:
                self.log.error("GitError:\n" + e.error)
                self.write_error(400)

        try:
            username = self.get_current_user()["name"]
        except TypeError as e:
            self.log.error(e)
            raise HTTPError(HTTPStatus.INTERNAL_SERVER_ERROR, reason=e)

        url = f'/user/{username}/lab/tree/{lecture["code"]}/{assignment["id"]}/{quote(notebook_name)}'
        self.log.info(f"Redirecting to {url}")
        self.redirect(url)
