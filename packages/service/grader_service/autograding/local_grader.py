# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import fnmatch
import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from sqlalchemy.orm import Session
from traitlets.config import Config
from traitlets.config.configurable import LoggingConfigurable
from traitlets.traitlets import Int, TraitError, Type, Unicode, validate

from grader_service.autograding.git_manager import GitSubmissionManager
from grader_service.autograding.utils import collect_logs, executable_validator, rmtree
from grader_service.convert.converters.autograde import Autograde
from grader_service.convert.gradebook.models import GradeBookModel
from grader_service.orm.assignment import Assignment
from grader_service.orm.submission import AutoStatus, ManualStatus, Submission
from grader_service.orm.submission_logs import SubmissionLogs
from grader_service.orm.submission_properties import SubmissionProperties


class LocalAutogradeExecutor(LoggingConfigurable):
    """
    Runs an autograde job on the local machine
    with the current Python environment.
    Sets up the necessary directories
    and the gradebook JSON file used by :mod:`grader_service.convert`.
    """

    relative_input_path = Unicode("convert_in", allow_none=True).tag(config=True)
    relative_output_path = Unicode("convert_out", allow_none=True).tag(config=True)
    git_manager_class = Type(GitSubmissionManager, allow_none=False).tag(config=True)

    cell_timeout = Int(
        allow_none=False,
        help="Returns the cell timeout in seconds, either user-defined, from configuration or default values.",
    ).tag(config=True)

    default_cell_timeout = Int(300, help="Default cell timeout in seconds, defaults to 300").tag(
        config=True
    )

    min_cell_timeout = Int(10, help="Min cell timeout in seconds, defaults to 10.").tag(config=True)

    max_cell_timeout = Int(
        86400, help="Max cell timeout in seconds, defaults to 86400 (24 hours)"
    ).tag(config=True)

    def __init__(
        self, grader_service_dir: str, submission: Submission, close_session: bool = True, **kwargs
    ):
        """
        Creates the executor in the input
        and output directories that are specified
        by :attr:`base_input_path` and :attr:`base_output_path`.
        The grader service directory is used for accessing
        the git repositories to push the grading results.
        The database session is retrieved from the submission object.
        The associated session of the submission has to be available
        and must not be closed beforehand.

        :param grader_service_dir: The base directory of the whole
        grader service specified in the configuration.
        :type grader_service_dir: str
        :param submission: The submission object
        which should be graded by the executor.
        :type submission: Submission
        :param close_session: Whether to close the db session after grading.
        :type close_session: bool
        """
        super().__init__(**kwargs)
        self.grader_service_dir = grader_service_dir
        self.submission = submission
        self.assignment: Assignment = submission.assignment
        self.session: Session = Session.object_session(self.submission)
        # close session after grading (might need session later)
        self.close_session = close_session

        self.grading_logs: Optional[str] = None
        # Git manager performs the git operations when creating a new repo for the grading results
        self.git_manager = self.git_manager_class(grader_service_dir, self.submission)

        self.cell_timeout = self._determine_cell_timeout()

    def start(self):
        """
        Starts the autograding job.
        This is the only method that is exposed to the client.
        """
        self.log.info(
            "Starting autograding job for submission %s in %s",
            self.submission.id,
            self.__class__.__name__,
        )
        try:
            self._clean_up_input_and_output_dirs()
            self.git_manager.pull_submission(self.input_path)

            autograding_start = datetime.now()
            self._write_gradebook(self._put_grades_in_assignment_properties())
            self._run()
            autograding_finished = datetime.now()

            files_to_commit = self._get_whitelisted_files()
            self.git_manager.push_results(files_to_commit, self.output_path)
            self._set_properties()
            self._set_db_state()
        except Exception as e:
            self.log.error(
                "Failed autograding job for submission %s in %s",
                self.submission.id,
                self.__class__.__name__,
                exc_info=True,
            )
            if isinstance(e, subprocess.CalledProcessError):
                err_msg = e.stderr
            else:
                err_msg = str(e)
            self.grading_logs = (self.grading_logs or "") + err_msg
            self._set_db_state(success=False)
        else:
            ts = round((autograding_finished - autograding_start).total_seconds())
            self.log.info(
                "Successfully completed autograding job for submission %s in %s; took %s min %s s",
                self.submission.id,
                self.__class__.__name__,
                ts // 60,
                ts % 60,
            )
        finally:
            self._update_submission_logs()
            self._cleanup()

    @property
    def input_path(self):
        return os.path.join(
            self.grader_service_dir, self.relative_input_path, f"submission_{self.submission.id}"
        )

    @property
    def output_path(self):
        return os.path.join(
            self.grader_service_dir, self.relative_output_path, f"submission_{self.submission.id}"
        )

    def _clean_up_input_and_output_dirs(self):
        """Prepare clean input and output dirs before the autograde process"""
        if os.path.exists(self.input_path):
            rmtree(self.input_path)
        os.makedirs(self.input_path)
        if os.path.exists(self.output_path):
            rmtree(self.output_path)
        os.makedirs(self.output_path)

    def _write_gradebook(self, gradebook_str: str) -> None:
        """
        Writes the gradebook to the output directory where it will be used by
        :mod:`grader_service.convert` to load the data.
        The name of the written file is gradebook.json.
        :param gradebook_str: The content of the gradebook.
        :return: None
        """
        path = os.path.join(self.output_path, "gradebook.json")
        self.log.info(f"Writing gradebook to {path}")
        with open(path, "w") as f:
            f.write(gradebook_str)

    def _run(self):
        """
        Runs the autograding in the current interpreter
        and captures the output.
        """
        autograder = Autograde(
            self.input_path,
            self.output_path,
            "*.ipynb",
            assignment_settings=self.assignment.settings,
            config=self._get_autograde_config(),
        )

        # Add a handler to the autograder's logger so that we can capture its logs and write them
        # to self.grading_logs:
        with collect_logs(autograder.log) as log_stream:
            autograder.start()
            self.grading_logs = log_stream.getvalue()

    def _put_grades_in_assignment_properties(self) -> str:
        """
        Checks if assignment was already graded and returns updated properties.
        :return: str
        """
        if self.submission.manual_status == ManualStatus.NOT_GRADED:
            return self.assignment.properties

        assignment_properties = json.loads(self.assignment.properties)
        submission_properties = json.loads(self.submission.properties.properties)
        notebooks = set.intersection(
            set(assignment_properties["notebooks"].keys()),
            set(submission_properties["notebooks"].keys()),
        )
        for notebook in notebooks:
            # Set grades
            assignment_properties["notebooks"][notebook]["grades_dict"] = submission_properties[
                "notebooks"
            ][notebook]["grades_dict"]
            # Set comments
            assignment_properties["notebooks"][notebook]["comments_dict"] = submission_properties[
                "notebooks"
            ][notebook]["comments_dict"]

        self.log.info("Added grades dict to properties")
        properties_str = json.dumps(assignment_properties)
        return properties_str

    def _get_autograde_config(self) -> Config:
        """Returns the autograde config, with the timeout set for ExecutePreprocessor."""
        c = Config()
        c.ExecutePreprocessor.timeout = self.cell_timeout
        return c

    def _get_whitelist_patterns(self) -> set[str]:
        """Return the glob patterns which are used for whitelisting the generated autograded files."""
        return self.assignment.get_whitelist_patterns()

    def _get_whitelisted_files(self) -> List[str]:
        """
        Prepares a list of shell-escaped filenames matching the whitelist patterns of the assignment.

        The list can be directly passed to the `git commit` command.

        :return: list of shell-escaped filenames matching the whitelist patterns of the assignment
        """
        file_patterns = self._get_whitelist_patterns()
        if not file_patterns:
            # No filtering needed
            return ["."]

        files_to_commit = []

        # get all files in the directory
        for root, dirs, files in os.walk(self.output_path):
            # Exclude .git directory - it contains subdirectories which we don't need to check
            if ".git" in root:
                continue
            rel_root = os.path.relpath(root, self.output_path)
            for file in files:
                file_path = os.path.join(rel_root, file) if rel_root != "." else file
                if any(fnmatch.fnmatch(file_path, pattern) for pattern in file_patterns):
                    files_to_commit.append(file_path)

        return files_to_commit

    def _set_properties(self) -> None:
        """
        Loads the contents of the gradebook.json file
        and sets them as the submission properties.
        Also calculates the score of the submission
        after autograding based on the updated properties.

        :return: None
        """
        with open(os.path.join(self.output_path, "gradebook.json"), "r") as f:
            gradebook_str = f.read()

        properties = SubmissionProperties(properties=gradebook_str, sub_id=self.submission.id)

        self.session.merge(properties)

        gradebook_dict = json.loads(gradebook_str)
        book = GradeBookModel.from_dict(gradebook_dict)
        score = 0
        for id, n in book.notebooks.items():
            score += n.score
        self.submission.grading_score = score
        self.submission.score = self.submission.score_scaling * score
        self.session.commit()

    def _set_db_state(self, success=True) -> None:
        """
        Sets the submission autograding status based on the success parameter
        and sets the logs from autograding.

        :param success: Whether the grading process was a success or failure.
        :return: None
        """
        if success:
            self.submission.auto_status = AutoStatus.AUTOMATICALLY_GRADED
        else:
            self.submission.auto_status = AutoStatus.GRADING_FAILED
        self.session.commit()

    def _update_submission_logs(self):
        if self.grading_logs is not None:
            # Remove null characters to avoid database storage/string processing/display/etc. issues
            self.grading_logs = self.grading_logs.replace("\x00", "")
        logs = SubmissionLogs(logs=self.grading_logs, sub_id=self.submission.id)
        self.session.merge(logs)
        self.session.commit()

    def _cleanup(self) -> None:
        """
        Removes all files from the input and output directories
        and closes the session if specified by self.close_session.

        Note: This also removes the gradebook.json file, which is in the `self.output_path` dir.
        :return: None
        """
        try:
            shutil.rmtree(self.input_path)
            shutil.rmtree(self.output_path)
        except FileNotFoundError:
            pass
        if self.close_session:
            self.session.close()

    def _determine_cell_timeout(self):
        cell_timeout = self.default_cell_timeout
        # check if the cell timeout was set by user
        if self.assignment.settings.cell_timeout is not None:
            custom_cell_timeout = self.assignment.settings.cell_timeout
            self.log.info(
                f"Found custom cell timeout in assignment settings: {custom_cell_timeout} seconds."
            )
            cell_timeout = min(
                self.max_cell_timeout, max(custom_cell_timeout, self.min_cell_timeout)
            )
            self.log.info(f"Setting custom cell timeout to {cell_timeout}.")

        return cell_timeout

    @validate("min_cell_timeout", "default_cell_timeout", "max_cell_timeout")
    def _validate_cell_timeouts(self, proposal):
        trait_name = proposal["trait"].name
        value = proposal["value"]

        # Get current or proposed values
        min_t = value if trait_name == "min_cell_timeout" else self.min_cell_timeout
        default_t = value if trait_name == "default_cell_timeout" else self.default_cell_timeout
        max_t = value if trait_name == "max_cell_timeout" else self.max_cell_timeout

        # Validate the constraint
        if not (0 < min_t < default_t < max_t):
            raise TraitError(
                f"Invalid {trait_name} value ({value}). "
                f"Timeout values must satisfy: 0 < min_cell_timeout < default_cell_timeout < max_cell_timeout. "
                f"Got min={min_t}, default={default_t}, max={max_t}."
            )

        return value

    @validate("relative_input_path", "relative_output_path")
    def _validate_service_dir(self, proposal):
        path: str = proposal["value"]
        if not os.path.exists(self.grader_service_dir + "/" + path):
            self.log.info(f"Path {path} not found, creating new directories.")
            Path(path).mkdir(parents=True, exist_ok=True, mode=0o700)
        if not os.path.isdir(self.grader_service_dir + "/" + path):
            raise TraitError("The path has to be an existing directory")
        return path

    @validate("convert_executable")
    def _validate_executable(self, proposal):
        return executable_validator(proposal)


class LocalAutogradeProcessExecutor(LocalAutogradeExecutor):
    """Runs an autograde job on the local machine
    with the default Python environment in a separate process.
    Sets up the necessary directories
    and the gradebook JSON file used by :mod:`grader_service.convert`.
    """

    convert_executable = Unicode("grader-convert", allow_none=False).tag(config=True)

    def _run(self):
        """
        Runs the autograding in a separate python interpreter
        as a sub-process and captures the output.
        """
        command = [
            self.convert_executable,
            "autograde",
            "-i",
            self.input_path,
            "-o",
            self.output_path,
            "-p",
            "*.ipynb",
            f"--ExecutePreprocessor.timeout={self.cell_timeout}",
        ]
        self.log.info(f"Running {command}")
        process = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=None, text=True
        )
        self.grading_logs = process.stderr
        if process.returncode == 0:
            self.log.info(self.grading_logs)
            self.log.info("Process has successfully completed execution!")
        else:
            self.log.error(self.grading_logs)
            raise RuntimeError("Process has failed execution!")
