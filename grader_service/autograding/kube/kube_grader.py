# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import asyncio
from asyncio import Task, run

from kubernetes.client import (V1Pod, CoreV1Api, V1ObjectMeta,
                               V1PodStatus, ApiException)
from traitlets import Callable, Unicode, Integer, List, Dict
from traitlets.config import LoggingConfigurable

from grader_service.autograding.local_grader import LocalAutogradeExecutor
                                                     
import kubernetes.watch  
from grader_service.orm import Lecture, Submission
from grader_service.orm import Assignment


class GraderPod(LoggingConfigurable):
    """
    Wrapper for a kubernetes pod that supports polling of the pod's status.
    """
    poll_interval = Integer(default_value=1000,
                            allow_none=False,
                            help="Time in ms to wait before "
                                 "status is polled again.").tag(config=True)

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
        w = kubernetes.watch.Watch()
        
        try:
            for event in w.stream(self._client.read_namespaced_pod_status, 
                                  name=meta.name, 
                                  namespace=meta.namespace,
                                  timeout_seconds=1200):  # Optional timeout

                pod = event['object']
                status: V1PodStatus = pod.status
                
                if status.phase in ["Succeeded", "Failed"]:
                    w.stop()  # Stop watching once the pod is done
                    return status.phase

                # Continue watching for other states like Running, Pending, etc.
                
        except ApiException as e:
            self.log.error(f"Error watching pod status: {e}")
            raise

        finally:
            w.stop()  # Ensure watch is stopped if something goes wrong


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

    image_config_path = Unicode(default_value=None,
                                allow_none=True).tag(config=True)
    resolve_image_name = Callable(default_value=_get_image_name,
                                  allow_none=False).tag(config=True)
    kube_context = Unicode(default_value=None, allow_none=True,
                           help="Kubernetes context to load config from. "

                                "If the context is None (default), "
                                "the incluster config "
                                "will be used.").tag(config=True)

    resolve_node_selector = Callable(default_value=lambda _: None, allow_none=False,
                                     help="""Function that takes a lecture as input and outputs a node selector for 
                                     this lecture. The returned value has to be a dict[str, str] or None and is directly 
                                     passed to the Kubernetes API.""").tag(config=True)

    volume = Dict(default_value={},
                  allow_none=False).tag(config=True)

    extra_volumes = List(default_value=[],
                         allow_none=False).tag(config=True)

    extra_volume_mounts = List(default_value=[],
                               allow_none=False).tag(config=True)

    convert_executable = Unicode("grader-convert",
                                 allow_none=False).tag(config=True)

    namespace = Unicode(default_value=None, allow_none=True,
                        help="Namespace to deploy grader pods into. "
                             "If changed, correct roles to Serviceaccount "
                             "need to be applied.").tag(config=True)
    uid = Integer(default_value=1000, allow_none=False,
                  help="The User ID for the grader container").tag(config=True)

    def __init__(self, grader_service_dir: str,
                 submission: Submission, **kwargs):
        super().__init__(grader_service_dir, submission, **kwargs)
        self.lecture = self.assignment
