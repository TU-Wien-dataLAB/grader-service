# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import io
import logging
import os
from typing import Any, List

from traitlets import Unicode

from grader_service.autograding.local_grader import GitSubmissionManager, LocalAutogradeExecutor
from grader_service.convert.converters.generate_feedback import GenerateFeedback
from grader_service.handlers.handler_utils import GitRepoType
from grader_service.orm.submission import FeedbackStatus, Submission


class FeedbackGitSubmissionManager(GitSubmissionManager):
    """Git manager for generating submission feedback."""

    input_repo_type = GitRepoType.AUTOGRADE
    output_repo_type = GitRepoType.FEEDBACK

    def __init__(self, grader_service_dir: str, submission: Submission, **kwargs: Any):
        super().__init__(grader_service_dir, submission, **kwargs)
        self.input_branch = f"submission_{self.submission.commit_hash}"
        self.output_branch = f"feedback_{self.submission.commit_hash}"


class GenerateFeedbackExecutor(LocalAutogradeExecutor):
    git_manager_class = FeedbackGitSubmissionManager
    input_repo_type = GitRepoType.AUTOGRADE
    output_repo_type = GitRepoType.FEEDBACK

    @property
    def input_path(self):
        return os.path.join(
            self.grader_service_dir, self.relative_input_path, f"feedback_{self.submission.id}"
        )

    @property
    def output_path(self):
        return os.path.join(
            self.grader_service_dir, self.relative_output_path, f"feedback_{self.submission.id}"
        )

    def _run(self):
        properties_str = self.submission.properties.properties
        self._write_gradebook(properties_str)

        feedback_generator = GenerateFeedback(
            self.input_path,
            self.output_path,
            "*.ipynb",
            assignment_settings=self.assignment.settings,
        )

        log_stream = io.StringIO()
        log_handler = logging.StreamHandler(log_stream)
        log_handler.setFormatter(
            logging.Formatter(
                fmt="[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
            )
        )
        feedback_generator.log.addHandler(log_handler)

        try:
            feedback_generator.start()
        finally:
            self.grading_logs = (self.grading_logs or "") + log_stream.getvalue()
            feedback_generator.log.removeHandler(log_handler)

    def _get_whitelisted_files(self) -> List[str]:
        # No need to filter files against a whitelist when generating feedback.
        return ["."]

    def _set_properties(self) -> None:
        # No need to set properties. Only remove the gradebook file.
        os.unlink(os.path.join(self.output_path, "gradebook.json"))

    def _set_db_state(self, success=True) -> None:
        """
        Sets the submission feedback status based on the success of the generation.

        :param success: Whether feedback generation was successful or not.
        :return: None
        """
        if success:
            self.submission.feedback_status = FeedbackStatus.GENERATED
        else:
            self.submission.feedback_status = FeedbackStatus.GENERATION_FAILED
        self.session.commit()


class GenerateFeedbackProcessExecutor(GenerateFeedbackExecutor):
    convert_executable = Unicode("grader-convert", allow_none=False).tag(config=True)

    def _run(self):
        self._write_gradebook(self.submission.properties)

        command = (
            f"{self.convert_executable} generate_feedback -i "
            f'"{self.input_path}" -o "{self.output_path}" -p "*.ipynb"'
        )
        self.log.info(f"Running {command}")
        process = self._run_subprocess(command, None)
        self.grading_logs = process.stderr.read().decode("utf-8")
        self.log.info(self.grading_logs)
        if process.returncode == 0:
            self.log.info("Process has successfully completed execution!")
        else:
            raise RuntimeError("Process has failed execution!")
