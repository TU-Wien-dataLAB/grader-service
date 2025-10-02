# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import fnmatch
import json
import os
import shlex
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

from sqlalchemy.orm import Session
from traitlets.config import Config
from traitlets.config.configurable import LoggingConfigurable
from traitlets.traitlets import Callable, TraitError, Type, Unicode, validate

from grader_service.autograding.utils import collect_logs, rmtree
from grader_service.convert.converters.autograde import Autograde
from grader_service.convert.gradebook.models import GradeBookModel
from grader_service.handlers.handler_utils import GitRepoType
from grader_service.orm.assignment import Assignment
from grader_service.orm.lecture import Lecture
from grader_service.orm.submission import AutoStatus, ManualStatus, Submission
from grader_service.orm.submission_logs import SubmissionLogs
from grader_service.orm.submission_properties import SubmissionProperties


def default_timeout_func(lecture: Lecture) -> int:
    return 360


def executable_validator(proposal: dict) -> str:
    exec: str = proposal["value"]
    if shutil.which(exec) is None:
        raise TraitError(f"The executable is not valid: {exec}")
    return exec


class GitSubmissionManager(LoggingConfigurable):
    """
    Handles git-related operations performed by autograder executors.
    """

    git_executable = Unicode("git", allow_none=False).tag(config=True)
    input_repo_type = Unicode(GitRepoType.USER, allow_none=False).tag(config=True)
    output_repo_type = Unicode(GitRepoType.AUTOGRADE, allow_none=False).tag(config=True)

    def __init__(self, grader_service_dir: str, submission: Submission, **kwargs: Any):
        super().__init__(**kwargs)
        self.grader_service_dir = grader_service_dir
        self.submission = submission

        if self.input_repo_type == GitRepoType.USER and self.submission.edited:
            # User's submission was edited by the instructor - repo type has to be adjusted
            self.input_repo_type = GitRepoType.EDIT

        self.input_branch = "main"
        self.output_branch = f"submission_{self.submission.commit_hash}"

    def _get_repo_path(self, repo_type: GitRepoType) -> str:
        """Determines the Git repository path for the submission."""
        assignment: Assignment = self.submission.assignment
        lecture: Lecture = assignment.lecture
        repo_name = self.submission.user.name

        base_repo_path = os.path.join(
            self.grader_service_dir, "git", lecture.code, str(assignment.id), repo_type
        )
        if repo_type == GitRepoType.AUTOGRADE:
            return os.path.join(base_repo_path, "user", repo_name)
        elif repo_type == GitRepoType.EDIT:
            return os.path.join(base_repo_path, str(self.submission.id))
        elif repo_type == GitRepoType.USER:
            return os.path.join(base_repo_path, repo_name)
        else:
            raise ValueError(f"Cannot determine repo path for repo type {repo_type}")

    def pull_submission(self, input_path: str) -> None:
        """Inits and pulls the submission repository into the input path.

        :param input_path: The directory where the input repo will be created.
        """
        input_repo_path = self._get_repo_path(self.input_repo_type)

        self.log.info(f"Pulling repo {input_repo_path} into input directory")
        commands = [
            f"{self.git_executable} init",
            f'{self.git_executable} pull "{input_repo_path}" {self.input_branch}',
        ]

        # When autograding a user's submission, check out to the commit of submission
        if self.input_repo_type == GitRepoType.USER:
            commands.append(f"{self.git_executable} checkout {self.submission.commit_hash}")

        for cmd in commands:
            self.log.info(f"Running {cmd}")
            self._run_git(cmd, input_path)

        self.log.info("Successfully cloned repo.")

    def _set_up_output_repo(self, output_path: str) -> None:
        """Initializes the output repo and switches to a separate branch named
        after the commit hash of the submission."""
        output_repo_path = self._get_repo_path(self.output_repo_type)

        if not os.path.exists(output_repo_path):
            os.makedirs(output_repo_path)
            self._run_git(f'{self.git_executable} init --bare "{output_repo_path}"', output_path)

        command = f"{self.git_executable} init"
        self.log.info(f"Running {command} at {output_path}")
        self._run_git(command, output_path)
        self.log.info(f"Creating the new branch {self.output_branch} and switching to it")
        command = f"{self.git_executable} switch -c {self.output_branch}"
        self._run_git(command, output_path)
        self.log.info(f"Now at branch {self.output_branch}")

    def _commit_files(self, filenames: List[str], output_path: str) -> None:
        """
        Commits the provided files in the repo at `output_path`.
        """
        self.log.info(f"Committing files in {output_path}")

        if not filenames:
            self.log.info("No files to commit.")
            return

        self._run_git(f"{self.git_executable} add -- " + " ".join(filenames), output_path)
        self._run_git(
            f'{self.git_executable} commit -m "{self.submission.commit_hash}"', output_path
        )

    def push_results(self, filenames: List[str], output_path: str) -> None:
        """Creates the output repository, commits and pushes the changes."""
        self._set_up_output_repo(output_path)
        self._commit_files(filenames, output_path)

        output_repo_path = self._get_repo_path(self.output_repo_type)

        self.log.info(f"Pushing to {output_repo_path} at branch {self.output_branch}")
        command = f'{self.git_executable} push -uf "{output_repo_path}" {self.output_branch}'
        self.log.info(f"Running {command}")
        self._run_git(command, output_path)
        self.log.info("Pushing complete")

    def _run_git(self, command: str, cwd: Optional[str]) -> None:
        """
        Execute a git command as a subprocess.

        :param command: The command to execute as a string.
        :param cwd: The working directory the subprocess should run in.
        """
        try:
            subprocess.run(
                [self.git_executable, *shlex.split(command)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd,
                text=True,  # Decodes output to string
                check=True,  # Raises a CalledProcessError on non-zero exit code
            )
        except subprocess.CalledProcessError as e:
            self.log.error(e.stderr)
            raise
        except Exception as e:
            self.log.error(e)
            raise

    # TODO: Can I decorate executable_validator with both "git_executable" and "convert_executable"?
    @validate("git_executable")
    def _validate_executable(self, proposal):
        return executable_validator(proposal)


class LocalAutogradeExecutor(LoggingConfigurable):
    """
    Runs an autograde job on the local machine
    with the current Python environment.
    Sets up the necessary directories
    and the gradebook JSON file used by :mod:`grader_service.convert`.
    """

    relative_input_path = Unicode("convert_in", allow_none=True).tag(config=True)
    relative_output_path = Unicode("convert_out", allow_none=True).tag(config=True)
    # TODO: verify that this is the appropriate traitlet
    git_manager_class = Type(GitSubmissionManager, allow_none=False).tag(config=True)

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
        super().__init__(**kwargs)
        self.grader_service_dir = grader_service_dir
        self.submission = submission
        self.assignment: Assignment = submission.assignment
        self.session: Session = Session.object_session(self.submission)
        # close session after grading (might need session later)
        self.close_session = close_session

        self.grading_logs: Optional[str] = None

        self.git_manager = self.git_manager_class(grader_service_dir, self.submission)

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
            self.log.error(err_msg)
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
        properties_str = self._put_grades_in_assignment_properties()
        self._write_gradebook(properties_str)

        autograder = Autograde(
            self.input_path,
            self.output_path,
            "*.ipynb",
            assignment_settings=self.assignment.settings,
            config=self._get_autograde_config(),
        )

        # Add a handler to the autograder's logger so that we can capture its logs and add them
        # to self.grading_logs:
        with collect_logs(autograder.log) as log_stream:
            autograder.start()
            self.grading_logs = (self.grading_logs or "") + log_stream.getvalue()

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
        """Returns the autograde config, with the timeout function for ExecutePreprocessor."""
        c = Config()
        c.ExecutePreprocessor.timeout = self.timeout_func(self.assignment.lecture)
        return c

    def _get_whitelisted_files(self) -> List[str]:
        """
        Prepares a list of shell-escaped filenames matching the whitelist patterns of the assignment.

        The list can be directly passed to the `git commit` command.

        :return: list of shell-escaped filenames matching the whitelist patterns of the assignment
        """
        file_patterns = self.assignment.get_whitelist_patterns()
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

        # escape filenames to handle special characters and whitespaces
        escaped_files = [shlex.quote(f) for f in files_to_commit]

        return escaped_files

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
        """
        self._write_gradebook(self._put_grades_in_assignment_properties())

        command = [
            self.convert_executable,
            "autograde",
            "-i",
            self.input_path,
            "-o",
            self.output_path,
            "-p",
            "*.ipynb",
            f"--ExecutePreprocessor.timeout={self.timeout_func(self.assignment.lecture)}",
        ]
        self.log.info(f"Running {command}")
        process = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=None, text=True
        )
        self.grading_logs = process.stderr
        self.log.info(self.grading_logs)
        if process.returncode == 0:
            self.log.info("Process has successfully completed execution!")
        else:
            raise RuntimeError("Process has failed execution!")
