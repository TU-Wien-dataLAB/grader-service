import traitlets.config

from grader_service.autograding.local_grader import LocalAutogradeExecutor
from grader_service.handlers.base_handler import GraderBaseHandler, authorize
from grader_service.orm.takepart import Scope
from grader_service.registry import VersionSpecifier, register_handler


def _get_effective_executor_value(
    app_cfg: traitlets.config.Config, executor_class: type[LocalAutogradeExecutor], trait_name: str
):
    """
    Return the configured value for trait_name if present in app_cfg,
    otherwise return the class default pulled from the trait metadata.
    """

    # 1) retrieve the provided class field from the config
    executor_class_field = app_cfg.get(executor_class.__name__, None)

    # executor_class_field may be None, or a Config object / dict-like. Use mapping access.
    if executor_class_field is not None and trait_name in executor_class_field:
        return executor_class_field.get(trait_name)

    # 2) fallback to the trait's default from the class metadata
    return executor_class.class_traits()[trait_name].default()


@register_handler(path=r"\/api\/config\/?", version_specifier=VersionSpecifier.ALL)
class ConfigHandler(GraderBaseHandler):
    """
    Handler class for requests to /config
    """

    @authorize([Scope.tutor, Scope.instructor])
    async def get(self):
        app_cfg = self.application.config
        executor_class = app_cfg.RequestHandlerConfig.autograde_executor_class

        def resolve(name):
            return _get_effective_executor_value(app_cfg, executor_class, name)

        self.write_json(
            {
                "default_cell_timeout": resolve("default_cell_timeout"),
                "min_cell_timeout": resolve("min_cell_timeout"),
                "max_cell_timeout": resolve("max_cell_timeout"),
            }
        )
