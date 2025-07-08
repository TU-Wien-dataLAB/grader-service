# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import fnmatch
import io
import json
import logging
import os
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from subprocess import CalledProcessError
from typing import List, Optional, Set

from sqlalchemy.orm import Session
from traitlets.config import Config
from traitlets.config.configurable import LoggingConfigurable
from traitlets.traitlets import Callable, TraitError, Unicode, validate

from grader_service.autograding.utils import rmtree
from grader_service.convert.converters.autograde import Autograde
from grader_service.convert.gradebook.models import GradeBookModel
from grader_service.orm.assignment import Assignment
from grader_service.orm.lecture import Lecture
from grader_service.orm.submission import Submission
from grader_service.orm.submission_logs import SubmissionLogs
from grader_service.orm.submission_properties import SubmissionProperties


@dataclass
class AutogradingStatus:
    status: str
    started_at: datetime
    finished_at: datetime


def default_timeout_func(lecture: Lecture) -> int:
    return 360


class LocalAutogradeExecutor(LoggingConfigurable):
    """
    Runs an autograde job on the local machine
    with the current Python environment.
    Sets up the necessary directories
    and the gradebook JSON file used by :mod:`grader_service.convert`.
    """

    relative_input_path = Unicode("convert_in", allow_none=True).tag(config=True)
    relative_output_path = Unicode("convert_out", allow_none=True).tag(config=True)
    git_executable = Unicode("git", allow_none=False).tag(config=True)

    timeout_func = Callable(
        default_timeout_func,
        allow_none=False,
        help="Function that takes a lecture as an argument and returns the cell timeout in seconds.",
    ).tag(config=True)

    def __init__(
        self, grader_service_dir: str, submission: Submission, close_session=True, **kwargs
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
        """
        super(LocalAutogradeExecutor, self).__init__(**kwargs)
        self.grader_service_dir = grader_service_dir
        self.submission = submission
        self.assignment: Assignment = submission.assignment
        self.session: Session = Session.object_session(self.submission)
        # close session after grading (might need session later)
        self.close_session = close_session

        self.autograding_start: Optional[datetime] = None
        self.autograding_finished: Optional[datetime] = None
        self.autograding_status: Optional[str] = None
        self.grading_logs: Optional[str] = None

    def start(self):
        """
        Starts the autograding job.
        This is the only method that is exposed to the client.
        It re-raises all exceptions that happen while running.
        """
        self.log.info(
            f"Starting autograding job for submission "
            f"{self.submission.id} in {self.__class__.__name__}"
        )
        try:
            self._pull_submission()
            self.autograding_start = datetime.now()
            self._run()
            self.autograding_finished = datetime.now()
            self._set_properties()
            self._push_results()
            self._set_db_state()
            ts = round((self.autograding_finished - self.autograding_start).total_seconds())
            self.log.info(
                f"Successfully completed autograding job for submission "
                f"{self.submission.id} in {self.__class__.__name__};"
                + f" took {ts // 60}min {ts % 60}s"
            )
        except Exception:
            self.log.error(
                f"Failed autograding job for submission "
                f"{self.submission.id} in {self.__class__.__name__}",
                exc_info=True,
            )
            self._set_db_state(success=False)
        finally:
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

    def _write_gradebook(self, gradebook_str: str):
        """
        Writes the gradebook to the output directory where it will be used by
        :mod:`grader_service.convert` to load the data.
        The name of the written file is gradebook.json.
        :param gradebook_str: The content of the gradebook.
        :return: None
        """
        if not os.path.exists(self.output_path):
            os.mkdir(self.output_path)
        path = os.path.join(self.output_path, "gradebook.json")
        self.log.info(f"Writing gradebook to {path}")
        with open(path, "w") as f:
            f.write(gradebook_str)

    def _pull_submission(self):
        """
        Pulls the submission repository into the input path
        based on the assignment type.
        :return: Coroutine
        """
        if not os.path.exists(self.input_path):
            Path(self.input_path).mkdir(parents=True, exist_ok=True)

        assignment: Assignment = self.submission.assignment
        lecture: Lecture = assignment.lecture
        repo_name = self.submission.username

        if self.submission.edited:
            git_repo_path = os.path.join(
                self.grader_service_dir,
                "git",
                lecture.code,
                str(assignment.id),
                "edit",
                str(self.submission.id),
            )
        else:
            git_repo_path = os.path.join(
                self.grader_service_dir, "git", lecture.code, str(assignment.id), "user", repo_name
            )
        # clean start to autograde process
        if os.path.exists(self.input_path):
            rmtree(self.input_path)
        os.makedirs(self.input_path, exist_ok=True)
        if os.path.exists(self.output_path):
            rmtree(self.output_path)
        os.makedirs(self.output_path, exist_ok=True)

        self.log.info(f"Pulling repo {git_repo_path} into input directory")

        command = f"{self.git_executable} init"
        self.log.info(f"Running {command}")
        self._run_subprocess(command, self.input_path)

        command = f'{self.git_executable} pull "{git_repo_path}" main'
        self.log.info(f"Running {command}")
        self._run_subprocess(command, self.input_path)
        self.log.info("Successfully cloned repo")

        # Checkout to commit of submission except when it was manually edited
        if not self.submission.edited:
            command = f"{self.git_executable} checkout {self.submission.commit_hash}"
            self.log.info(f"Running {command}")
            self._run_subprocess(command, self.input_path)
            self.log.info(f"Now at commit {self.submission.commit_hash}")

    def _run(self):
        """
        Runs the autograding in the current interpreter
        and captures the output.
        :return: Coroutine
        """
        if os.path.exists(self.output_path):
            rmtree(self.output_path)

        os.makedirs(self.output_path, exist_ok=True)
        self._write_gradebook(self._put_grades_in_assignment_properties())

        c = Config()
        c.ExecutePreprocessor.timeout = self.timeout_func(self.assignment.lecture)

        autograder = Autograde(
            self.input_path,
            self.output_path,
            "*.ipynb",
            assignment_settings=self.assignment.settings,
            config=c,
        )
        autograder.force = True

        log_stream = io.StringIO()
        log_handler = logging.StreamHandler(log_stream)
        log_handler.setFormatter(
            logging.Formatter(
                fmt="[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
            )
        )
        autograder.log.addHandler(log_handler)

        try:
            autograder.start()
        finally:
            self.grading_logs = log_stream.getvalue()
            autograder.log.removeHandler(log_handler)

    def _put_grades_in_assignment_properties(self) -> str:
        """
        Checks if assignment was already graded and returns updated properties.
        :return: str
        """
        if self.submission.manual_status == "not_graded":
            return self.assignment.properties

        assignment_properties = json.loads(self.assignment.properties)
        submission_properties = json.loads(self.submission.properties.properties)
        notebooks = set.intersection(
            set(assignment_properties["notebooks"].keys()),
            set(submission_properties["notebooks"].keys()),
        )
        for notebook in notebooks:
            # Set grades
            #
            assignment_properties["notebooks"][notebook]["grades_dict"] = submission_properties[
                "notebooks"
            ][notebook]["grades_dict"]
            # Set comments
            assignment_properties["notebooks"][notebook]["comments_dict"] = submission_properties[
                "notebooks"
            ][notebook]["comments_dict"]

        properties_str = json.dumps(assignment_properties)
        self.log.info("Added grades dict to properties")
        return properties_str

    def _push_results(self):
        """
        Pushes the results to the autograde repository
        as a separate branch named after the commit hash of the submission.
        Removes the gradebook.json file before doing so.
        :return: Coroutine
        """
        os.unlink(os.path.join(self.output_path, "gradebook.json"))
        self.log.info(f"Pushing files: {os.listdir(self.output_path)}")

        assignment: Assignment = self.submission.assignment
        lecture: Lecture = assignment.lecture
        repo_name = self.submission.username

        git_repo_path = os.path.join(
            self.grader_service_dir,
            "git",
            lecture.code,
            str(assignment.id),
            "autograde",
            "user",
            repo_name,
        )

        if not os.path.exists(git_repo_path):
            os.makedirs(git_repo_path, exist_ok=True)
            try:
                self._run_subprocess(f'git init --bare "{git_repo_path}"', self.output_path)
            except CalledProcessError as e:
                raise e

        command = f"{self.git_executable} init"
        self.log.info(f"Running {command} at {self.output_path}")
        try:
            self._run_subprocess(command, self.output_path)
        except CalledProcessError as e:
            raise e

        self.log.info(f"Creating new branch submission_{self.submission.commit_hash}")
        command = f"{self.git_executable} switch -c submission_{self.submission.commit_hash}"
        try:
            self._run_subprocess(command, self.output_path)
        except CalledProcessError as e:
            raise e
        self.log.info(f"Now at branch submission_{self.submission.commit_hash}")
        self.commit_whitelisted_files()

        self.log.info(
            f"Pushing to {git_repo_path} at branch submission_{self.submission.commit_hash}"
        )
        command = (
            f"{self.git_executable} push -uf "
            f'"{git_repo_path}" submission_{self.submission.commit_hash}'
        )
        self.log.info(command)
        try:
            self._run_subprocess(command, self.output_path)
        except Exception:
            raise RuntimeError(f"Failed to push to {git_repo_path}")
        self.log.info("Pushing complete")

    def _get_whitelist_patterns(self) -> Set[str]:
        """
        Combines all whitelist patterns into a single set.
        """
        base_filter = ["*.ipynb"]
        extra_files = json.loads(self.assignment.properties).get("extra_files", [])
        allowed_file_patterns = self.assignment.settings.allowed_files

        return set(base_filter + extra_files + allowed_file_patterns)

    def _get_files_to_commit(self, file_patterns: Set[str]) -> List[str]:
        """
        Prepares a list of shell-escaped filenames matching the given patterns.

        :param file_patterns: set of patterns to match the filenames against
        :return: list of shell-escaped filenames
        """
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

        # escape filenames to handle special characters and whitespaces
        escaped_files = [shlex.quote(f) for f in files_to_commit]

        return escaped_files

    def commit_whitelisted_files(self):
        self.log.info(f"Committing filtered files in {self.output_path}")

        file_patterns = self._get_whitelist_patterns()
        files_to_commit = self._get_files_to_commit(file_patterns)

        if not files_to_commit:
            self.log.info("No files to commit.")
            return

        try:
            # add only the filtered files
            add_command = f"{self.git_executable} add -- " + " ".join(files_to_commit)
            self._run_subprocess(add_command, self.output_path)

            # commit files
            commit_command = f'{self.git_executable} commit -m "{self.submission.commit_hash}"'
            self._run_subprocess(commit_command, self.output_path)

        except CalledProcessError as e:
            err_msg = f"Failed to commit changes: {e.output}"
            self.log.error(err_msg)
            raise RuntimeError(err_msg)

    def _set_properties(self):
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

    def _set_db_state(self, success=True):
        """
        Sets the submission autograding status based on the success parameter
        and sets the logs from autograding.
        :param success: Whether the grading process was a success or failure.
        :return: None
        """
        if success:
            self.submission.auto_status = "automatically_graded"
        else:
            self.submission.auto_status = "grading_failed"

        if self.grading_logs is not None:
            self.grading_logs = self.grading_logs.replace("\x00", "")
        logs = SubmissionLogs(logs=self.grading_logs, sub_id=self.submission.id)
        self.session.merge(logs)
        self.session.commit()

    def _cleanup(self):
        """
        Removes all files from the input and output directories
        and closes the session if specified by self.close_session.
        :return: None
        """
        try:
            shutil.rmtree(self.input_path)
            shutil.rmtree(self.output_path)
        except FileNotFoundError:
            pass
        if self.close_session:
            self.session.close()

    def _run_subprocess(self, command: str, cwd: str) -> subprocess.CompletedProcess:
        """
        Execute the command as a subprocess.
        :param command: The command to execute as a string.
        :param cwd: The working directory the subprocess should run in.
        :return: CompletedProcess object which contains information about the execution.
        """
        try:
            result = subprocess.run(
                shlex.split(command),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd,
                text=True,  # Decodes output to string
                check=True,  # Raises a CalledProcessError on non-zero exit code
            )
            return result
        except subprocess.CalledProcessError as e:
            self.grading_logs = e.stderr
            self.log.error(self.grading_logs)
            raise
        except Exception as e:
            self.grading_logs = (self.grading_logs or "") + str(e)
            self.log.error(e)
            raise

    @validate("relative_input_path", "relative_output_path")
    def _validate_service_dir(self, proposal):
        path: str = proposal["value"]
        if not os.path.exists(self.grader_service_dir + "/" + path):
            self.log.info(f"Path {path} not found, creating new directories.")
            Path(path).mkdir(parents=True, exist_ok=True, mode=0o700)
        if not os.path.isdir(self.grader_service_dir + "/" + path):
            raise TraitError("The path has to be an existing directory")
        return path

    @validate("convert_executable", "git_executable")
    def _validate_executable(self, proposal):
        exec: str = proposal["value"]
        if shutil.which(exec) is None:
            raise TraitError(f"The executable is not valid: {exec}")
        return exec


class LocalProcessAutogradeExecutor(LocalAutogradeExecutor):
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

        :return: Coroutine
        """
        if os.path.exists(self.output_path):
            rmtree(self.output_path)

        os.mkdir(self.output_path)
        self._write_gradebook(self._put_grades_in_assignment_properties())

        command = (
            f"{self.convert_executable} autograde "
            f'-i "{self.input_path}" '
            f'-o "{self.output_path}" '
            f'-p "*.ipynb" '
            f"--ExecutePreprocessor.timeout={self.timeout_func(self.assignment.lecture)}"
        )
        self.log.info(f"Running {command}")
        process = self._run_subprocess(command, None)
        if process.returncode == 0:
            self.grading_logs = process.stderr.read().decode("utf-8")
            self.log.info(self.grading_logs)
            self.log.info("Process has successfully completed execution!")
        else:
            raise RuntimeError("Process has failed execution!")
