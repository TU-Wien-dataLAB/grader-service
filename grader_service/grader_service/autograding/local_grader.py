# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import io
import json
import logging
import os
import shlex
import shutil
import stat
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from re import S
from subprocess import PIPE, CalledProcessError
from typing import Optional

from grader_convert.converters.autograde import Autograde
from grader_convert.gradebook.models import GradeBookModel
from grader_service.orm.assignment import Assignment
from grader_service.orm.group import Group
from grader_service.orm.lecture import Lecture
from grader_service.orm.submission import Submission
from sqlalchemy.orm import Session
from tornado.process import Subprocess
from traitlets.config.configurable import LoggingConfigurable
from traitlets.traitlets import TraitError, Unicode, validate


def rm_error(func, path, exc_info):
    if not os.access(path, os.W_OK):
        # Is the error an access error ?
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise


@dataclass
class AutogradingStatus:
    status: str
    started_at: datetime
    finished_at: datetime


class LocalAutogradeExecutor(LoggingConfigurable):
    """Runs an autograde job on the local machine with the current Python environment.
    Sets up the necessary directories and the gradebook JSON file used by :mod:`grader_convert`.
    """
    base_input_path = Unicode(os.getenv("GRADER_AUTOGRADE_IN_PATH"), allow_none=False).tag(config=True)
    base_output_path = Unicode(os.getenv("GRADER_AUTOGRADE_OUT_PATH"), allow_none=False).tag(config=True)

    git_executable = Unicode("git", allow_none=False).tag(config=True)

    def __init__(self, grader_service_dir: str, submission: Submission, close_session=True, **kwargs):
        """Creates the executor in the input and output directories that are specified
        by :attr:`base_input_path` and :attr:`base_output_path`.
        The grader service directory is used for accessing the git repositories to push the grading results.
        The database session is retrieved from the submission object.
        The associated session of the submission has to be available and must not be closed beforehand.

        :param grader_service_dir: The base directory of the whole grader service specified in the configuration.
        :type grader_service_dir: str
        :param submission: The submission object which should be graded by the executor.
        :type submission: Submission
        """
        super(LocalAutogradeExecutor, self).__init__(**kwargs)
        self.grader_service_dir = grader_service_dir
        self.submission = submission
        self.session: Session = Session.object_session(self.submission)
        self.close_session = close_session  # close session after grading (might need session later)

        self.autograding_start: Optional[datetime] = None
        self.autograding_finished: Optional[datetime] = None
        self.autograding_status: Optional[str] = None
        self.grading_logs: Optional[str] = None

    async def start(self):
        """Starts the autograding job. This is the only method that is exposed to the client.
        It re-raises all exceptions that happen while running.
        """
        self.log.info(f"Starting autograding job for submission {self.submission.id} in {self.__class__.__name__}")
        try:
            await self._pull_submission()
            self.autograding_start = datetime.now()
            await self._run()
            self.autograding_finished = datetime.now()
            self._set_properties()
            await self._push_results()
            self._set_db_state()
            ts = round((self.autograding_finished - self.autograding_start).total_seconds())
            self.log.info(
                f"Successfully completed autograding job for submission {self.submission.id} in {self.__class__.__name__};"
                + f" took {ts // 60}min {ts % 60}s")
        except Exception:
            self.log.error(f"Failed autograding job for submission {self.submission.id} in {self.__class__.__name__}",
                           exc_info=True)
            self._set_db_state(success=False)
            # raise
        finally:
            self._cleanup()

    @property
    def input_path(self):
        return os.path.join(self.base_input_path, f"submission_{self.submission.id}")

    @property
    def output_path(self):
        return os.path.join(self.base_output_path, f"submission_{self.submission.id}")

    def _write_gradebook(self, gradebook_str: str):
        """
        Writes the gradebook to the output directory where it will be used by
        :mod:`grader_convert` to load the data.
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

    async def _pull_submission(self):
        """
        Pulls the submission repository into the input path based on the assignment type.

        :return: Coroutine
        """
        if not os.path.exists(self.input_path):
            Path(self.input_path).mkdir(parents=True, exist_ok=True)

        assignment: Assignment = self.submission.assignment
        lecture: Lecture = assignment.lecture

        if assignment.type == "user":
            repo_name = self.submission.username
        else:
            # TODO: fix query to work with group.name
            group = self.session.query(Group).get(
                (self.submission.username, lecture.id)
            )
            if group is None:
                raise ValueError()
            repo_name = group.name

        git_repo_path = os.path.join(
            self.grader_service_dir,
            "git",
            lecture.code,
            str(assignment.id),
            assignment.type,
            repo_name,
        )

        if os.path.exists(self.input_path):
            shutil.rmtree(self.input_path, onerror=rm_error)
        os.mkdir(self.input_path)

        self.log.info(f"Pulling repo {git_repo_path} into input directory")

        command = f"{self.git_executable} init"
        self.log.info(f"Running {command}")
        await self._run_subprocess(command, self.input_path)

        command = f'{self.git_executable} pull "{git_repo_path}" main'
        self.log.info(f"Running {command}")
        await self._run_subprocess(command, self.input_path)
        self.log.info("Successfully cloned repo")

        command = f"{self.git_executable} checkout {self.submission.commit_hash}"
        self.log.info(f"Running {command}")
        await self._run_subprocess(command, self.input_path)
        self.log.info(f"Now at commit {self.submission.commit_hash}")

        self.submission.auto_status = "pending"
        self.session.commit()

    async def _run(self):
        """
        Runs the autograding in the current interpreter and captures the output.

        :return: Coroutine
        """
        if os.path.exists(self.output_path):
            shutil.rmtree(self.output_path, onerror=rm_error)

        os.mkdir(self.output_path)
        self._write_gradebook(self.submission.assignment.properties)

        autograder = Autograde(self.input_path, self.output_path, "*.ipynb")
        autograder.force = True

        log_stream = io.StringIO()
        log_handler = logging.StreamHandler(log_stream)
        autograder.log.addHandler(log_handler)

        try:
            autograder.start()
        finally:
            self.grading_logs = log_stream.getvalue()
            autograder.log.removeHandler(log_handler)

    async def _push_results(self):
        """
        Pushes the results to the autograde repository as a separate branch named after the commit hash of
        the submission. Removes the gradebook.json file before doing so.
        :return: Coroutine
        """
        os.unlink(os.path.join(self.output_path, "gradebook.json"))

        assignment: Assignment = self.submission.assignment
        lecture: Lecture = assignment.lecture

        if assignment.type == "user":
            repo_name = self.submission.username
        else:
            group = self.session.query(Group).get(
                (self.submission.username, lecture.id)
            )
            if group is None:
                raise ValueError()
            repo_name = group.name

        git_repo_path = os.path.join(
            self.grader_service_dir,
            "git",
            lecture.code,
            str(assignment.id),
            "autograde",
            assignment.type,
            repo_name,
        )

        if not os.path.exists(git_repo_path):
            os.makedirs(git_repo_path, exist_ok=True)
            try:
                await self._run_subprocess(
                    f'git init --bare "{git_repo_path}"', self.output_path
                )
            except CalledProcessError:
                raise

        command = f"{self.git_executable} init"
        self.log.info(f"Running {command} at {self.output_path}")
        try:
            await self._run_subprocess(command, self.output_path)
        except CalledProcessError:
            pass

        self.log.info(f"Creating new branch submission_{self.submission.commit_hash}")
        command = (
            f"{self.git_executable} switch -c submission_{self.submission.commit_hash}"
        )
        try:
            await self._run_subprocess(command, self.output_path)
        except CalledProcessError:
            pass
        self.log.info(f"Now at branch submission_{self.submission.commit_hash}")

        self.log.info(f"Commiting all files in {self.output_path}")
        try:
            await self._run_subprocess(
                f"{self.git_executable} add -A", self.output_path
            )
            await self._run_subprocess(
                f'{self.git_executable} commit -m "{self.submission.commit_hash}"',
                self.output_path,
            )
        except CalledProcessError:
            raise RuntimeError(f"Failed to commit changes")

        self.log.info(
            f"Pushing to {git_repo_path} at branch submission_{self.submission.commit_hash}"
        )
        command = f'{self.git_executable} push -uf "{git_repo_path}" submission_{self.submission.commit_hash}'
        try:
            await self._run_subprocess(command, self.output_path)
        except CalledProcessError:
            raise RuntimeError(f"Failed to push to {git_repo_path}")
        self.log.info("Pushing complete")

    def _set_properties(self):
        """
        Loads the contents of the gradebook.json file and sets them as the submission properties.
        Also calculates the score of the submission after autograding based on the updated properties.
        :return: None
        """
        with open(os.path.join(self.output_path, "gradebook.json"), "r") as f:
            gradebook_str = f.read()
        self.submission.properties = gradebook_str
        gradebook_dict = json.loads(gradebook_str)
        book = GradeBookModel.from_dict(gradebook_dict)
        score = 0
        for id, n in book.notebooks.items():
            score += n.score
        self.submission.score = score
        self.session.commit()

    def _set_db_state(self, success=True):
        """
        Sets the submission autograding status based on the success parameter and sets the logs from autograding.
        :param success: Whether the grading process was a success or failure.
        :return: None
        """
        if success:
            self.submission.auto_status = "automatically_graded"
        else:
            self.submission.auto_status = "grading_failed"
        self.submission.logs = self.grading_logs
        self.session.commit()

    def _cleanup(self):
        """
        Removes all files from the input and output directories and closes the session if
        specified by self.close_session.
        :return: None
        """
        try:
            shutil.rmtree(self.input_path)
            shutil.rmtree(self.output_path)
        except FileNotFoundError:
            pass
        if self.close_session:
            self.session.close()

    async def _run_subprocess(self, command: str, cwd: str) -> Subprocess:
        """
        Execute the command as a subprocess.
        :param command: The command to execute as a string.
        :param cwd: The working directory the subprocess should run in.
        :return: Coroutine which resolves to a Subprocess object which resulted from the execution.
        """
        try:
            process = Subprocess(shlex.split(command), stdout=PIPE, stderr=PIPE, cwd=cwd)
            await process.wait_for_exit()
        except CalledProcessError:
            self.grading_logs = process.stderr.read().decode("utf-8")
            self.log.error(self.grading_logs)
        except FileNotFoundError as e:
            self.grading_logs = str(e)
            self.log.error(self.grading_logs)
            raise e
        return process

    @validate("base_input_path", "base_output_path")
    def _validate_service_dir(self, proposal):
        path: str = proposal["value"]
        if not os.path.isabs(path):
            raise TraitError("The path specified has to be absolute")
        if not os.path.exists(path):
            self.log.info(f"Path {path} not found, creating new directories.")
            Path(path).mkdir(parents=True, exist_ok=True, mode=664)
        if not os.path.isdir(path):
            raise TraitError("The path has to be an existing directory")
        return path

    @validate("convert_executable", "git_executable")
    def _validate_executable(self, proposal):
        exec: str = proposal["value"]
        if shutil.which(exec) is None:
            raise TraitError(f"The executable is not valid: {exec}")
        return exec


class LocalProcessAutogradeExecutor(LocalAutogradeExecutor):
    """Runs an autograde job on the local machine with the default Python environment in a separate process.
    Sets up the necessary directories and the gradebook JSON file used by :mod:`grader_convert`.
    """

    convert_executable = Unicode("grader-convert", allow_none=False).tag(config=True)

    async def _run(self):
        """
        Runs the autograding in a separate python interpreter as a sub-process and captures the output.

        :return: Coroutine
        """
        if os.path.exists(self.output_path):
            shutil.rmtree(self.output_path, onerror=rm_error)

        os.mkdir(self.output_path)
        self._write_gradebook(self.submission.assignment.properties)

        command = f'{self.convert_executable} autograde -i "{self.input_path}" -o "{self.output_path}" -p "*.ipynb"'
        self.log.info(f"Running {command}")
        process = await self._run_subprocess(command, None)
        if process.returncode == 0:
            self.grading_logs = process.stderr.read().decode("utf-8")
            self.log.info(self.grading_logs)
            self.log.info("Process has successfully completed execution!")
        else:
            raise RuntimeError("Process has failed execution!")
