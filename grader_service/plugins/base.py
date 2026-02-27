# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Plugin base classes and plugin manager for the Grader Service.

The plugin system follows a simple registration pattern:

1. Subclass :class:`GraderPlugin` and set the ``name`` class attribute.
2. Decorate the class with :func:`register_plugin` so it is discovered
   at import time.
3. Call :func:`create_plugin_manager` during application startup to
   instantiate all registered plugins and collect them in a
   :class:`PluginManager`.

Handlers access plugins via ``self.application.plugin_manager.get("name")``
and celery tasks via ``self.celery.plugin_manager.get("name")``.
"""

import logging
from typing import Dict, Iterator, List, Optional, Type

from traitlets.config import LoggingConfigurable

_PLUGIN_REGISTRY: List[Type["GraderPlugin"]] = []


class GraderPlugin(LoggingConfigurable):
    """Base class for all Grader Service plugins.

    Subclasses **must** define a ``name`` class-level attribute (a unique
    string identifier such as ``"lti"``).

    Plugins are created during application startup by
    :func:`create_plugin_manager` and then stored in a :class:`PluginManager`
    on the application object.  Handlers and tasks look up plugins via that
    manager instead.
    """

    name: str = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.name:
            raise ValueError(
                f"{self.__class__.__name__} must define a non-empty 'name' class attribute"
            )


def register_plugin(cls: Type[GraderPlugin]) -> Type[GraderPlugin]:
    """Class decorator that registers a plugin class for auto-discovery.

    Usage::

        @register_plugin
        class MyPlugin(GraderPlugin):
            name = "my_plugin"
            ...
    """
    if not issubclass(cls, GraderPlugin):
        raise TypeError(f"{cls.__name__} must be a subclass of GraderPlugin")
    _PLUGIN_REGISTRY.append(cls)
    return cls


class PluginManager:
    """Registry that holds live plugin instances keyed by name.

    Created once per process (web server or celery worker) and stored on
    the application object so that handlers and tasks can look up plugins
    without relying on global singletons.
    """

    def __init__(self) -> None:
        self._plugins: Dict[str, GraderPlugin] = {}
        self.log = logging.getLogger(__name__)

    # -- mutation -----------------------------------------------------------

    def register(self, plugin: GraderPlugin) -> None:
        """Register a plugin instance."""
        if plugin.name in self._plugins:
            self.log.warning("Plugin '%s' already registered - replacing", plugin.name)
        self._plugins[plugin.name] = plugin
        self.log.info("Registered plugin: %s (%s)", plugin.name, type(plugin).__name__)

    # -- lookup -------------------------------------------------------------

    def get(self, name: str) -> Optional[GraderPlugin]:
        """Return a plugin by *name*, or ``None`` if not found."""
        return self._plugins.get(name)

    def __getitem__(self, name: str) -> GraderPlugin:
        return self._plugins[name]

    def __contains__(self, name: str) -> bool:
        return name in self._plugins

    def __iter__(self) -> Iterator[GraderPlugin]:
        return iter(self._plugins.values())

    def __len__(self) -> int:
        return len(self._plugins)

    @property
    def names(self) -> List[str]:
        """Return the names of all registered plugins."""
        return list(self._plugins.keys())


def create_plugin_manager(config=None, log=None) -> PluginManager:
    """Instantiate all registered plugins and return a populated
    :class:`PluginManager`.

    This should be called once during application startup (both in the
    web server and in celery workers).

    Parameters
    ----------
    config : traitlets.config.Config, optional
        The application configuration object.  Each plugin receives this so
        that traitlets config keys (e.g. ``c.LTISyncGrades.systems``) are
        automatically applied.
    log : logging.Logger, optional
        Logger for error reporting during plugin creation.
    """
    manager = PluginManager()
    _log = log or logging.getLogger(__name__)

    for cls in _PLUGIN_REGISTRY:
        try:
            kwargs = {}
            if config is not None:
                kwargs["config"] = config
            plugin = cls(**kwargs)
            manager.register(plugin)
        except Exception:
            _log.exception(f"Failed to create plugin {cls.__name__}")

    return manager
