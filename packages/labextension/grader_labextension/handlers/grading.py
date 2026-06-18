# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
import os
import shutil
import urllib.parse

from grader_service.errors import APIError
from grader_service.handlers import GitRepoType
from tornado.httpclient import HTTPResponse
from tornado.web import HTTPError, authenticated

from grader_labextension.handlers.base_handler import ExtensionBaseHandler
from grader_labextension.registry import register_handler
from grader_labextension.services.git import GitError, GitService
from grader_labextension.services.request import RequestService, RequestServiceError


@register_handler(
    path=r"api\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/submissions\/save?"
)
class ExportGradesHandler(ExtensionBaseHandler):
    """
    Tornado Handler class for http requests to /lectures/{lecture_id}/assignments/{assignment_id}/submissions/save.
    """

    async def put(self, lecture_id: int, assignment_id: int):
        """
        Exports submissions of an assignment to the csv format.

        :param lecture_id: id of the lecture
        :param assignment_id: id of the assignment
        :return: the csv content
        """
        query_params = RequestService.get_query_string(
            {
                "instructor-version": "true",
                "filter": self.get_argument("filter", "none"),
                "format": "csv",
            }
        )
        try:
            response: HTTPResponse = await self.request_service.request(
                method="GET",
                endpoint=f"{self.service_base_url}api/lectures/{lecture_id}/assignments/{assignment_id}/submissions{query_params}",
                header=self.grader_authentication_header,
                decode_response=False,
            )
        except RequestServiceError as e:
            self.log.error(e)
            raise HTTPError(e.code, reason=e.message)

        lecture = await self.get_lecture(lecture_id)
        assignment = await self.get_assignment(lecture_id, assignment_id)
        dir_path = os.path.join(
            self.root_dir, lecture["code"], "assignments", str(assignment["id"])
        )
        os.makedirs(dir_path, exist_ok=True)
        csv_content = response.body.decode("utf-8")
        parsed_query_params = urllib.parse.parse_qs(query_params.lstrip("?"))
        filter_value = parsed_query_params.get("filter", ["none"])[0]
        file_path = os.path.join(dir_path, f"{assignment['name']}_{filter_value}_submissions.csv")
        with open(file_path, "w") as f:
            f.write(csv_content)

        self.write({"status": "OK"})


@register_handler(
    path=r"api\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/grading\/(?P<sub_id>\d*)\/auto\/?"
)
class GradingAutoHandler(ExtensionBaseHandler):
    """
    Tornado Handler class for http requests to
    /lectures/{lecture_id}/assignments/{assignment_id}/submissions/{submission_id}/auto.
    """

    @authenticated
    async def get(self, lecture_id: int, assignment_id: int, sub_id: int):
        """Sends a GET-request to the grader service to autograde a submission

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        :param sub_id: id of the submission
        :type sub_id: int
        """
        try:
            response = await self.request_service.request(
                method="GET",
                endpoint=f"{self.service_base_url}api/lectures/{lecture_id}/assignments/{assignment_id}/grading/{sub_id}/auto",
                header=self.grader_authentication_header,
            )
        except RequestServiceError as e:
            self.log.error(e)
            raise HTTPError(e.code, reason=e.message)
        self.write(response)


@register_handler(
    path=r"api\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/grading\/(?P<sub_id>\d*)\/manual\/?"
)
class GradingManualHandler(ExtensionBaseHandler):
    """
    Tornado Handler class for http requests to
    /lectures/{lecture_id}/assignments/{assignment_id}/submissions/{submission_id}/manual.
    """

    @authenticated
    async def get(self, lecture_id: int, assignment_id: int, sub_id: int):
        """Generates a local git repository and pulls autograded or original files of a submission in the user directory

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        :param sub_id: id of the submission
        :type sub_id: int
        """
        query_params = RequestService.get_query_string({"lecture_id": lecture_id})
        try:
            lecture = await self.get_lecture(lecture_id)

            assignment = await self.get_assignment(lecture_id, assignment_id)

            submission = await self.request_service.request(
                "GET",
                f"{self.service_base_url}api/lectures/{lecture_id}/assignments/{assignment_id}/submissions/{sub_id}",
                header=self.grader_authentication_header,
            )
        except RequestServiceError as e:
            self.log.error(e)
            raise HTTPError(e.code, reason=e.message)

        repo_type = None
        submission_user = None
        # only pull from user repo if the submission hasn't been autograded (happens when autograde_type is unassisted)
        # or when autograding has failed (we still want to allow manual grading in that case)
        if (
            submission["auto_status"] == "not_graded"
            or submission["auto_status"] == "grading_failed"
        ):
            repo_type = GitRepoType.USER
            # retrieve user whose repo we want to pull from
            submission_user = await self.request_service.request(
                "GET",
                f"{self.service_base_url}api/users/{submission['user_id']}{query_params}",
                header=self.grader_authentication_header,
            )
        else:
            repo_type = GitRepoType.AUTOGRADE

        git_service = GitService(
            server_root_dir=self.root_dir,
            lecture_code=lecture["code"],
            assignment_id=assignment["id"],
            repo_type=repo_type,
            config=self.config,
        )
        git_service.path = os.path.join(
            git_service.git_root_dir,
            git_service.lecture_code,
            "manualgrade",
            str(git_service.assignment_id),
            str(sub_id),
        )
        self.log.info(f"Path: {git_service.path}")
        if os.path.exists(git_service.path):
            shutil.rmtree(git_service.path, ignore_errors=True)

        os.makedirs(git_service.path, exist_ok=True)
        try:
            if not git_service.is_git():
                git_service.init()
            if repo_type == GitRepoType.AUTOGRADE:
                git_service.set_remote(GitRepoType.AUTOGRADE, additional_path=str(sub_id))
                git_service.pull(
                    GitRepoType.AUTOGRADE, branch=f"submission_{submission['commit_hash']}"
                )
                self.log.info(f"Pulled AUTOGRADE repo for submission {submission['id']}")
            elif repo_type == GitRepoType.USER:
                git_service.set_remote(GitRepoType.USER, additional_path=submission_user["name"])
                git_service.pull(GitRepoType.USER)
                git_service.go_to_commit(submission["commit_hash"])
                self.log.info(f"Pulled USER repo for submission {submission['id']}")
        except GitError as e:
            self.log.error(f"Git error: {e.error}")
            raise APIError(502, reason="git process failed", message=e.error)


@register_handler(
    path=r"api\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/grading\/(?P<sub_id>\d*)\/feedback\/?"
)
class GenerateFeedbackHandler(ExtensionBaseHandler):
    """
    Tornado Handler class for http requests to
    /lectures/{lecture_id}/assignments/{assignment_id}/submissions/{submission_id}/feedback.
    """

    @authenticated
    async def get(self, lecture_id: int, assignment_id: int, sub_id: int):
        """Sends a GET-request to the grader service to generate feedback for a graded submission

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        :param sub_id: id of the submission
        :type sub_id: int
        """

        try:
            response = await self.request_service.request(
                method="GET",
                endpoint=f"{self.service_base_url}api/lectures/{lecture_id}/assignments/{assignment_id}/grading/{sub_id}/feedback",
                header=self.grader_authentication_header,
            )
        except RequestServiceError as e:
            self.log.error(e)
            raise HTTPError(e.code, reason=e.message)
        self.write(response)


@register_handler(
    path=r"api\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/grading\/(?P<sub_id>\d*)\/pull\/feedback\/?"
)
class PullFeedbackHandler(ExtensionBaseHandler):
    """
    Tornado Handler class for http requests to
    /lectures/{lecture_id}/assignments/{assignment_id}/submissions/{submission_id}/pull/feedback.
    """

    @authenticated
    async def get(self, lecture_id: int, assignment_id: int, sub_id: int):
        """Generates a local git repository and pulls the feedback files of a submission in the user directory

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        :param sub_id: id of the submission
        :type sub_id: int
        """
        try:
            lecture = await self.get_lecture(lecture_id)

            assignment = await self.get_assignment(lecture_id, assignment_id)

            submission = await self.request_service.request(
                "GET",
                f"{self.service_base_url}api/lectures/{lecture_id}/assignments/{assignment_id}/submissions/{sub_id}",
                header=self.grader_authentication_header,
            )
        except RequestServiceError as e:
            self.log.error(e)
            raise HTTPError(e.code, reason=e.message)

        git_service = GitService(
            server_root_dir=self.root_dir,
            lecture_code=lecture["code"],
            assignment_id=assignment["id"],
            repo_type=GitRepoType.FEEDBACK,
            config=self.config,
        )
        git_service.path = os.path.join(
            git_service.git_root_dir,
            git_service.lecture_code,
            "feedback",
            str(git_service.assignment_id),
            str(sub_id),
        )
        self.log.info(f"Path: {git_service.path}")
        if not os.path.exists(git_service.path):
            os.makedirs(git_service.path, exist_ok=True)

        if not git_service.is_git():
            git_service.init()
        git_service.set_remote(GitRepoType.FEEDBACK, additional_path=str(sub_id))
        git_service.pull(
            GitRepoType.FEEDBACK, branch=f"feedback_{submission['commit_hash']}", force=True
        )
        self.write({"status": "Pulled Feedback"})
