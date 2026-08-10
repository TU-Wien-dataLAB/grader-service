# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
import os
import subprocess

from traitlets.traitlets import Unicode

from grader_service.autograding.local_grader import LocalAutogradeExecutor
from grader_service.convert.converters.generate_feedback import GenerateFeedback
from grader_service.repo_types import GitRepoType
from grader_service.orm.submission import FeedbackStatus, AutoStatus, ManualStatus


class LocalFeedbackExecutor(LocalAutogradeExecutor):
    output_repo_type = GitRepoType.FEEDBACK

    @property
    def input_repo_type(self):
        if (
            self.submission.auto_status in [AutoStatus.NOT_GRADED, AutoStatus.GRADING_FAILED]
            and self.submission.manual_status == ManualStatus.MANUALLY_GRADED
        ):
            # When submission hasn't been autograded or autograding failed,
            # pull from user repo to generate feedback
            return GitRepoType.USER
        return GitRepoType.AUTOGRADE

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
        feedback_generator = GenerateFeedback(
            self.input_path,
            self.output_path,
            "*.ipynb",
            assignment_settings=self.assignment.settings,
        )
        feedback_generator.start()

    def _put_grades_in_assignment_properties(self) -> str:
        # No need to calculate the properties again when generating feedback.
        return self.submission.properties.properties

    def _get_whitelist_patterns(self) -> set[str]:
        # We only want to commit html files when generating feedback.
        return {"*.html"}

    def _set_properties(self) -> None:
        # No need to set properties.
        pass

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

    def _update_submission_logs(self):
        # No need to collect feedback logs.
        pass


class LocalFeedbackProcessExecutor(LocalFeedbackExecutor):
    convert_executable = Unicode("grader-convert", allow_none=False).tag(config=True)

    def _run(self):
        command = [
            self.convert_executable,
            "generate_feedback",
            "-i",
            self.input_path,
            "-o",
            self.output_path,
            "-p",
            "*.ipynb",
        ]
        self.log.info(f"Running {command}")
        process = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=None, text=True
        )
        if process.returncode == 0:
            self.log.info(process.stderr)
            self.log.info("Process has successfully completed execution!")
        else:
            self.log.error(process.stderr)
            raise RuntimeError("Process has failed execution!")
