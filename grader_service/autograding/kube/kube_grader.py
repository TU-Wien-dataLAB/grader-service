# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import asyncio
import inspect
import json
import os
import re
import time
from asyncio import Task, run

from kubernetes import config
from kubernetes.client import ApiException, CoreV1Api, V1EnvVar, V1ObjectMeta, V1Pod
from traitlets import Callable, Dict, Integer, List, Unicode
from traitlets.config import LoggingConfigurable
from urllib3.exceptions import MaxRetryError

from grader_service.autograding.kube.util import get_current_namespace, make_pod
from grader_service.autograding.local_grader import LocalAutogradeExecutor
from grader_service.autograding.utils import rmtree
from grader_service.orm import Assignment, Lecture, Submission
from grader_service.orm.assignment import json_serial


class GraderPod(LoggingConfigurable):
    """
    Wrapper for a kubernetes pod that supports polling of the pod's status.
    """

    poll_interval = Integer(
        default_value=5, allow_none=False, help="Time in sec to wait before status is polled again."
    ).tag(config=True)
    max_grading_time = Integer(
        default_value=3600,
        allow_none=False,
        help="Maximal grading time in sec before the grading fails",
    ).tag(config=True)

    def __init__(self, pod: V1Pod, api: CoreV1Api, **kwargs):
        super().__init__(**kwargs)
        self.pod = pod
        self._client = api
        # Ensure the event loop exists or create a new one
        try:
            self.loop = asyncio.get_event_loop()
        except RuntimeError:
            # Create a new event loop if none exists
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
        self._polling_task = self.loop.create_task(self._poll_status())

    def stop_polling(self) -> None:
        self._polling_task.cancel()

    def poll(self) -> str:
        return self.loop.run_until_complete(self.polling)

    @property
    def polling(self) -> Task:
        return self._polling_task

    @property
    def name(self) -> str:
        return self.pod.metadata.name

    @property
    def namespace(self) -> str:
        return self.pod.metadata.namespace

    # Watch for pod status changes instead of polling in intervals.
    async def _poll_status(self) -> str:
        meta: V1ObjectMeta = self.pod.metadata
        start_time = time.time()
        interval = self.poll_interval
        timeout = self.max_grading_time

        while True:
            # Read the pod status using read_namespaced_pod_status
            pod_status = self._client.read_namespaced_pod_status(
                name=meta.name, namespace=meta.namespace
            )

            # Extract the pod phase (status)
            phase = pod_status.status.phase
            self.log.debug(f"Pod {meta.name} is currently in {phase} phase.")

            # Exit conditions
            if phase in ["Succeeded", "Failed"]:  # Stop polling if pod completes or fails
                self.log.info(f"Pod {meta.name} has finished with phase: {phase}.")
                return phase

            # Check if timeout is reached
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout:
                print(f"Polling timed out after {timeout} seconds.")
                return "Failed"

            # Wait for the next poll
            time.sleep(interval)


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


class KubeAutogradeExecutor(LocalAutogradeExecutor):
    """
    Runs an autograde job in a kubernetes cluster as a pod.
    The cluster has to have a shared persistent
    volume claim that is mounted in the input
    and output directories so that both the service and
    the executor pods have access to the files.
    The service account of the grader service has to have
    permission to get, update, create and delete pods, pod status and pod logs.
    """

    # Annotations to attach to the Kubernetes pod
    annotations = Dict(
        default_value={},
        allow_none=True,
        help="Annotations to associate with the pod. Defaults to an empty dictionary.",
    ).tag(config=True)

    # Name of the executable for converting the grader
    convert_executable = Unicode(
        "grader-convert",
        allow_none=False,
        help="The executable name for the grader container conversion. Defaults to 'grader-convert'.",
    ).tag(config=True)

    # List of extra volumes to attach to the pod
    extra_volumes = List(
        default_value=[],
        allow_none=False,
        help="List of extra volumes to attach to the pod. Defaults to an empty list.",
    ).tag(config=True)

    # List of extra volume mounts to attach to the container
    extra_volume_mounts = List(
        default_value=[],
        allow_none=False,
        help="List of extra volume mounts for the container. Defaults to an empty list.",
    ).tag(config=True)

    # Configuration for the image name, with a callable for resolution
    image_config_path = Unicode(
        default_value=None,
        allow_none=True,
        help="Deprecated in v0.7, will be removed in v0.8, use pre_spawn_hook to dynamically change the autograding pod image.",
    ).tag(config=True)

    # Image pull policy for the Kubernetes pod
    image_pull_policy = Unicode(
        default_value="Always",
        allow_none=False,
        help="The image pull policy for the pod. Defaults to 'Always'.",
    ).tag(config=True)

    # Dictionary to store image pull secrets, helpful when pulling from private registries
    image_pull_secrets = List(
        default_value=[],
        help="""Autograding pod image pull secrets list (str). 
                                      Used for pulling images from private registries. Defaults to None.""",
        key_trait=Unicode(),
        value_trait=Unicode(),
        allow_none=True,
    ).tag(config=True)

    # Kubernetes context to load configuration from (in-cluster if None)
    kube_context = Unicode(
        default_value=None,
        allow_none=True,
        help="Kubernetes context to load the config from. If None, the in-cluster config is used.",
    ).tag(config=True)

    # Labels to attach to the Kubernetes pod
    labels = Dict(
        default_value={},
        allow_none=True,
        help="Labels to associate with the pod. Defaults to an empty dictionary.",
    ).tag(config=True)

    # Namespace where grader pods will be deployed
    namespace = Unicode(
        default_value=None,
        allow_none=True,
        help="Namespace for deploying grader pods. If None, the current namespace will be used. "
        "If changed, roles for ServiceAccount need to be applied.",
    ).tag(config=True)

    # Pre-spawn Hook configuration
    pre_spawn_hook = Callable(
        default_value=None,
        allow_none=True,
        help="""
        A callable function that executes before the autograding pod spawns. 
        Use this hook to customize pod configurations based on the specific lecture and assignment.

        **Parameters:**
        - `lecture` (Lecture): The lecture associated with the submission.
        - `assignment` (Assignment): The assignment associated with the submission.
        - `autograding_pod` (V1Pod): The current Kubernetes pod object for autograding.
        **Returns:**
        - V1Pod spec for autograding pod
        **Purpose:**
        This hook allows dynamic modification of pod specifications, such as:
        - Updating selectors.
        - Changing the container image.
        - Adjusting resource requests and limits.
        
        **Default:**
        None (no modifications will be applied unless a callable is provided).
        """,
    ).tag(config=True)

    # Callable to resolve the image name
    resolve_image_name = Callable(
        default_value=_get_image_name,
        allow_none=False,
        help="Deprecated in v0.7, will be removed in v0.8, use pre_spawn_hook to dynamically change the autograding pod image.",
    ).tag(config=True)

    # Callable for resolving node selector for a lecture
    resolve_node_selector = Callable(
        default_value=lambda _: None,
        allow_none=False,
        help="""Deprecated in v0.7, will be removed in v0.8, use pre_spawn_hook to dynamically set the node selectors of autograding pods.""",
    ).tag(config=True)

    # Tolerations for the autograding pod
    tolerations = Dict(
        default_value=None,
        help="""Autograding pod tolerations dictionary (str, str). 
                               Used to schedule pods on nodes with specific taints. Defaults to None.""",
        key_trait=Unicode(),
        value_trait=Unicode(),
        allow_none=True,
    ).tag(config=True)

    # User ID for the grader container (used to set user permissions inside the container)
    uid = Integer(
        default_value=1000,
        allow_none=False,
        help="User ID for the grader container. Defaults to 1000.",
    ).tag(config=True)

    # Dictionary for additional volume configuration
    volume = Dict(
        default_value={},
        allow_none=False,
        help="Dictionary for volume configuration. Defaults to an empty dictionary.",
    ).tag(config=True)

    def __init__(self, grader_service_dir: str, submission: Submission, **kwargs):
        super().__init__(grader_service_dir, submission, **kwargs)
        self.lecture = self.assignment.lecture
        if self.kube_context is None:
            self.log.info(
                f"Loading in-cluster config for kube executor of submission {self.submission.id}"
            )
            config.load_incluster_config()
        else:
            self.log.info(
                f"Loading cluster config '{self.kube_context}' "
                f"for kube executor of submission {self.submission.id}"
            )
            config.load_kube_config(context=self.kube_context)
        self.client = CoreV1Api()
        if self.namespace is None:
            self.log.info(f"Setting Namespace for submission {self.submission.id}")
            self.namespace = get_current_namespace()

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

    def get_autograde_pod_name(self) -> str:
        # sanitize username by converting to lowercase and replacing non-alphanumeric chars
        sanitized_username = re.sub(r"[^a-zA-Z0-9]+", "-", self.submission.username.lower())

        # truncate if too long to meet k8s pod name limits
        max_username_length = 50
        sanitized_username = sanitized_username[:max_username_length]

        # trim leading/trailing hyphens
        sanitized_username = sanitized_username.strip("-")

        return f"autograde-job-{sanitized_username}-{self.submission.id}"

    def create_env(self) -> list[V1EnvVar]:
        env = [
            V1EnvVar(
                name="ASSIGNMENT_SETTINGS",
                value=json.dumps(self.assignment.settings.to_dict(), default=json_serial),
            )
        ]
        return env

    def start_pod(self) -> GraderPod:
        """
        Starts a pod in the namespace
        with the commit hash as the name of the pod.
        The image is determined by the get_image method.
        :return:
        """
        # set standard config
        command = [
            self.convert_executable,
            "autograde",
            "-i",
            self.input_path,
            "-o",
            self.output_path,
            "-p",
            "*.ipynb",
            "--log-level=INFO",
            f"--ExecutePreprocessor.timeout={self.timeout_func(self.assignment.lecture)}",
        ]
        volumes = [self.volume] + self.extra_volumes
        volume_mounts = [
            {
                "name": "data",
                "mountPath": self.input_path,
                "subPath": self.relative_input_path + "/submission_" + str(self.submission.id),
            },
            {
                "name": "data",
                "mountPath": self.output_path,
                "subPath": self.relative_output_path + "/submission_" + str(self.submission.id),
            },
        ]
        volume_mounts = volume_mounts + self.extra_volume_mounts

        env = self.create_env()

        # create pod spec
        pod = make_pod(
            name=self.get_autograde_pod_name(),
            cmd=command,
            env=env,
            image=self.get_image(),
            image_pull_policy=self.image_pull_policy,
            image_pull_secrets=self.image_pull_secrets,
            working_dir="/",
            volumes=volumes,
            volume_mounts=volume_mounts,
            labels=self.labels,
            annotations=self.annotations,
            node_selector=self.resolve_node_selector(self.lecture),
            tolerations=self.tolerations,
            run_as_user=self.uid,
        )
        # run prespawn hook if it exists
        if callable(self.pre_spawn_hook):
            self.log.info(f"Running pre spawn hook for pod {pod.metadata.name}")
            pod = self.pre_spawn_hook(self.lecture, self.assignment, pod)

        # run grading pod
        self.log.info(f"Starting pod {pod.metadata.name} with command: {command}")
        pod = self.client.create_namespaced_pod(namespace=self.namespace, body=pod)
        # handle state of grading pod
        return GraderPod(pod, self.client, config=self.config)

    def _run(self):
        """
        Runs the autograding process in a kubernetes pod
        which has to have access to the files in the
        input and output directory through a persistent volume claim.
        :return: Coroutine
        """
        if os.path.exists(self.output_path):
            rmtree(self.output_path)
        os.makedirs(self.output_path, exist_ok=True)
        self._write_gradebook(self._put_grades_in_assignment_properties())
        grader_pod = None
        try:
            grader_pod = self.start_pod()
            self.log.info(f"Started pod {grader_pod.name} in namespace {grader_pod.namespace}")
            status = grader_pod.poll()
            self.grading_logs = self._get_pod_logs(grader_pod)
            self.log.info("Pod logs:\n" + self.grading_logs)
            if status == "Succeeded":
                self.log.info(f"Pod {grader_pod.name} has successfully completed execution!")
            else:
                self.log.error(f"Pod {grader_pod.name} has failed execution!")
                self._delete_pod(grader_pod)
                raise RuntimeError(f"Pod {grader_pod.name} has failed execution!")
            # cleanup
            self._delete_pod(grader_pod)
        except ApiException as e:
            error_message = json.loads(e.body)
            if error_message["reason"] != "AlreadyExists" and grader_pod is not None:
                try:
                    namespace = grader_pod.namespace
                    self.client.delete_namespaced_pod(name=grader_pod.name, namespace=namespace)
                except ApiException:
                    pass
            self.log.error(f"{error_message['reason']}: {error_message['message']}")
            raise RuntimeError("Pod has failed execution!")
        except MaxRetryError:
            self.log.error(
                "Kubernetes client could not connect to cluster! "
                "Is it running and specified correctly?"
            )
            raise RuntimeError("Pod has failed execution!")

    def _delete_pod(self, pod: GraderPod):
        """
        Deletes the pod from the cluster after successful or failed execution.
        :param pod: The pod to delete.
        :return: None
        """
        self.log.info(
            f"Deleting pod '{pod.name}' in namespace '{pod.namespace}' "
            f"after execution status {pod.polling.result()}"
        )
        self.client.delete_namespaced_pod(name=pod.name, namespace=pod.namespace)

    def _get_pod_logs(self, pod: GraderPod) -> str:
        """
        Returns the logs of the pod that were output during execution.
        :param pod: The pod to retrieve the logs from.
        :return: The logs as a string.
        """
        api_response: str = self.client.read_namespaced_pod_log(
            name=pod.name, namespace=pod.namespace
        )
        return api_response.strip()
