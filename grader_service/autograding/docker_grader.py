import abc
import inspect
import json
import os
import shutil
from asyncio import run

import docker
from docker.errors import ContainerError, ImageNotFound, APIError
from traitlets import Unicode, Callable, Dict, default

from grader_service.autograding.local_grader import LocalAutogradeExecutor, rm_error
from grader_service.orm import Submission, Lecture, Assignment


def _get_image_name(lecture: Lecture, assignment: Assignment = None) -> str:
    """
    Default implementation of the resolve_image_name method
    which return the lecture code followed by '_image'.
    All the functions have the lecture and assignment available as parameters.
    The function can either be sync or async.
    :param lecture: Lecture to build the image name.
    :param assignment: Assignment to build the image name.
    :return: The image name as a string.
    """
    return f"{lecture.code}_image"


class DockerImageExecutor(LocalAutogradeExecutor, abc.ABC):
    image_config_path = Unicode(default_value=None,
                                allow_none=True).tag(config=True)
    resolve_image_name = Callable(default_value=_get_image_name,
                                  allow_none=False).tag(config=True)

    def __init__(self, grader_service_dir: str, submission: Submission, close_session=True, **kwargs):
        super().__init__(grader_service_dir, submission, close_session, **kwargs)
        self.lecture = self.assignment.lecture

    def get_image(self) -> str:
        """
        Returns the image name based on the lecture and assignment.
        If an image config file exists and has
        been specified it will first be queried for an image name.
        If the image name cannot be found in the
        config file or none has been specified
        the image name will be determined by the resolve_image_name function
        which takes the lecture
        and assignment as parameters and is specified in the config.
        The default implementation of this function is to
         return the lecture code followed by '_image'.
        :return: The image name as determined by this method.
        """
        cfg = {}
        if self.image_config_path is not None:
            with open(self.image_config_path, "r") as f:
                cfg = json.load(f)
        try:
            lecture_cfg = cfg[self.lecture.code]
            if isinstance(lecture_cfg, str):
                return lecture_cfg
            else:
                return lecture_cfg[self.assignment.name]
        except KeyError:
            if inspect.iscoroutinefunction(self.resolve_image_name):
                return run(self.resolve_image_name(self.lecture, self.assignment))
            else:
                return self.resolve_image_name(self.lecture, self.assignment)


class DockerAutogradeExecutor(DockerImageExecutor):
    volumes = Dict().tag(config=True)

    @default("volumes")
    def _volumes(self):
        return {
            self.input_path: {'bind': f'/tmp/grader-service/{self.relative_input_path}', 'mode': 'ro'},
            self.output_path: {'bind': f'/tmp/grader-service/{self.relative_output_path}', 'mode': 'rw'}
        }

    def __init__(self, grader_service_dir: str, submission: Submission, close_session=True, **kwargs):
        super().__init__(grader_service_dir, submission, close_session, **kwargs)
        self.client = docker.from_env()

    async def _run(self):
        if os.path.exists(self.output_path):
            shutil.rmtree(self.output_path, onerror=rm_error)

        os.makedirs(self.output_path, exist_ok=True)
        self._write_gradebook(self._put_grades_in_assignment_properties())

        command = f'grader-convert autograde ' \
                  f'-i "{self.volumes[self.input_path]["bind"]}" ' \
                  f'-o "{self.volumes[self.output_path]["bind"]}" ' \
                  f'-p "*.ipynb" ' \
                  f'--copy_files={self.assignment.allow_files} ' \
                  f'--ExecutePreprocessor.timeout={self.timeout_func(self.assignment.lecture)}'
        image = self.get_image()

        self.log.info(f"Running {command} in docker container using image: {image}")
        try:
            self.grading_logs = self.client.containers.run(
                image=image,
                command=command,
                volumes=self.volumes,
                stdout=True,
                stderr=True,
                detach=False,
            )
            self.log.info(self.grading_logs)
            self.log.info("Container has successfully completed execution!")
        except ContainerError as e:
            self.log.error(f"Container {e.container} returned non-zero exit code! Logs:\n{e.stderr}")
            self.grading_logs = e.stderr
            raise RuntimeError("Container has failed execution!")
        except ImageNotFound as e:
            self.log.error(f"Could not find image {image} to run docker container!\n{e.explanation}")
            self.grading_logs = f"Could not find image to run docker container!\n{e.explanation}"
            raise RuntimeError("Container has failed execution!")
        except APIError as e:
            self.log.error(f"Docker API error: {e.explanation}")
            self.grading_logs = f"Docker API error: {e.explanation}"
            raise RuntimeError("Container has failed execution!")
