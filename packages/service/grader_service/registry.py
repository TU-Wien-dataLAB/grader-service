# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import enum
from typing import List, Tuple

from tornado.web import RequestHandler


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class HandlerPathRegistry(object, metaclass=Singleton):
    registry = {}

    @staticmethod
    def handler_list(base_url: str = "/") -> List[Tuple[str, RequestHandler]]:
        return list(
            zip(
                [
                    base_url.rstrip("/").replace("/", "\\/") + path
                    for path in HandlerPathRegistry.registry.values()
                ],
                HandlerPathRegistry.registry.keys(),
            )
        )

    @staticmethod
    def has_path(cls) -> bool:
        return cls in HandlerPathRegistry.registry

    @staticmethod
    def get_path(cls):
        return HandlerPathRegistry.registry[cls]

    @staticmethod
    def add(cls, path: str):
        # check if class inherits from tornado RequestHandler
        if RequestHandler not in cls.__mro__:
            err = "Incorrect base class. "
            err += "Class must be extended from tornado 'RequestHandler' "
            err += "to be registered."
            raise ValueError(err)
        HandlerPathRegistry.registry[cls] = path


class VersionSpecifier(enum.Enum):
    ALL = "all"
    NONE = "none"
    V1 = "1"


def register_handler(path: str, version_specifier: VersionSpecifier = VersionSpecifier.NONE):
    # TODO
    # add optional /services/grader prefix regex
    # any endpoint can also be accessed through /services/grader/<endpoint>
    # this enables the service to hide behind a jupyterhub as a managed service

    # add version specifier if set
    if version_specifier == VersionSpecifier.ALL:
        # only supports single digit versions
        excludes = ["all", "none"]
        values = [v.value for v in VersionSpecifier if v.value not in excludes]
        regex_versions = "".join(values)
        v = r"(?:\/v[{}])?".format(regex_versions)
    elif (version_specifier == VersionSpecifier.NONE) or (version_specifier is None):
        v = ""
    else:
        v = rf"\/v{version_specifier.value}"
    path = v + path

    def _register_class(cls):
        HandlerPathRegistry().add(cls, path)
        return cls

    return _register_class
