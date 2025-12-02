from grader_service.handlers.base_handler import GraderBaseHandler, authorize
from grader_service.orm.takepart import Scope
from grader_service.registry import VersionSpecifier, register_handler


def _get_effective_executor_value(app_cfg, executor_class, trait_name):
    """
    Return the configured value for trait_name if present in app_cfg,
    otherwise return the class default pulled from the trait metadata.
    """
    # app_cfg is a traitlets.config.Config object (mapping-like)
    # executor_class is the class (LocalAutogradeExecutor or similar)

    # 1) look up the per-class node as a mapping (not attribute access)
    user_node = app_cfg.get(executor_class.__name__, None)

    # user_node may be None, or a Config object / dict-like. Use mapping access.
    if user_node is not None and trait_name in user_node:
        # Use .get to return the exact user-supplied value (won't be a lazy object)
        return user_node.get(trait_name)

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
