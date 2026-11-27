# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.


from tornado.web import RequestHandler


class Singleton(type):
    _instances = {}  # noqa: RUF012

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class HandlerPathRegistry(metaclass=Singleton):
    registry = {}  # noqa: RUF012

    @staticmethod
    def handler_list(base_url) -> list[tuple[str, RequestHandler]]:
        return list(
            zip(
                [
                    base_url.replace("/", r"\/") + path
                    for path in HandlerPathRegistry.registry.values()
                ],
                HandlerPathRegistry.registry.keys(),
            )
        )

    @staticmethod
    def has_path(handler_cls) -> bool:
        return handler_cls in HandlerPathRegistry.registry

    @staticmethod
    def get_path(handler_cls):
        return HandlerPathRegistry.registry[handler_cls]

    @staticmethod
    def add(handler_cls, path: str):
        # check if class inherits from tornado RequestHandler
        if RequestHandler not in handler_cls.__mro__:
            raise ValueError(
                f"Incorrect base class. Class {handler_cls} has to be extended from tornado "
                f"'RequestHandler' in order to be registered."
            )
        HandlerPathRegistry.registry[handler_cls] = path


def register_handler(path: str):
    def _register_class(handler_cls):
        HandlerPathRegistry().add(handler_cls, path)
        return handler_cls

    return _register_class
