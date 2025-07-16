# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import asyncio
import inspect
import logging
import os
import secrets
import shutil
import signal
import subprocess
import sys

import tornado
import uvloop as uvloop
from jupyterhub.log import log_request
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from tornado.httpserver import HTTPServer
from traitlets import (
    Bool,
    Dict,
    Enum,
    HasTraits,
    Instance,
    Int,
    List,
    TraitError,
    Type,
    Unicode,
    config,
    default,
    observe,
    validate,
)
from traitlets import log as traitlets_log

from grader_service import __version__
from grader_service.auth.auth import Authenticator

# run __init__.py to register handlers
from grader_service.auth.dummy import DummyAuthenticator
from grader_service.autograding.celery.app import CeleryApp
from grader_service.handlers.base_handler import RequestHandlerConfig
from grader_service.handlers.static import CacheControlStaticFilesHandler
from grader_service.oauth2 import handlers as oauth_handlers
from grader_service.oauth2.provider import make_provider
from grader_service.orm import Lecture, Role, User
from grader_service.orm.base import DeleteState
from grader_service.orm.lecture import LectureState
from grader_service.orm.takepart import Scope
from grader_service.plugins.lti import LTISyncGrades
from grader_service.registry import HandlerPathRegistry
from grader_service.server import GraderServer
from grader_service.utils import url_path_join


def get_session_maker(url) -> scoped_session:
    engine = create_engine(url)
    return scoped_session(sessionmaker(bind=engine))


class GraderService(config.Application):
    name = "grader-service"
    version = __version__

    description = """Starts the grader service, which can be used to create
    and distribute assignments, collect submissions and grade them.
    """

    examples = """
  generate default config file:
      grader-service --generate-config -f /etc/grader/grader_service_config.py
  spawn the grader service:
      grader-service -f /etc/grader/grader_service_config.py
  """

    generate_config = Bool(False, help="Generate config file based on defaults.").tag(config=True)

    service_host = Unicode(
        os.getenv("GRADER_HOST", "0.0.0.0"), help="The host address of the service"
    ).tag(config=True)

    service_port = Int(
        int(os.getenv("GRADER_PORT", "4010")), help="The port the service runs on"
    ).tag(config=True)

    reuse_port = Bool(
        False, help="Whether to allow for the specified service port to be reused."
    ).tag(config=True)

    grader_service_dir = Unicode(os.getenv("GRADER_SERVICE_DIRECTORY"), allow_none=False).tag(
        config=True
    )

    db_url = Unicode(allow_none=False).tag(config=True)

    oauth_provider = None

    @default("db_url")
    def _default_db_url(self):
        db_path = os.path.join(self.grader_service_dir, "grader.db")
        service_dir_url = f"sqlite:///{db_path}"
        return os.getenv("GRADER_DB_URL", service_dir_url)

    grader_cookie_secret = Unicode(
        default_value=os.getenv("GRADER_COOKIE_SECRET", secrets.token_hex(nbytes=32)),
        allow_none=False,
    ).tag(config=True)

    max_body_size = Int(104857600, help="Sets the max buffer size in bytes, default to 100mb").tag(
        config=True
    )

    max_buffer_size = Int(104857600, help="Sets the max body size in bytes, default to 100mb").tag(
        config=True
    )

    service_git_username = Unicode("grader-service", allow_none=False).tag(config=True)

    service_git_email = Unicode("", allow_none=False).tag(config=True)

    config_file = Unicode("grader_service_config.py", help="The config file to load").tag(
        config=True
    )

    base_url_path = Unicode("/services/grader/", help="base url path", allow_none=False).tag(
        config=True
    )

    authenticator_class = Type(
        default_value=DummyAuthenticator,
        klass=Authenticator,
        allow_none=False,
        config=True,
        help="""
        The authenticator class to use for authentication.
        Default is DummyAuthenticator, which does not require a password by default.
        You can set this to your own authenticator class, which should inherit from Authenticator.
        """,
    )

    authenticator = Instance(klass=Authenticator)

    # TODO make configurable
    oauth_token_expires_in = int(1 * 24 * 3600)

    load_roles = Dict(
        Dict(),
        help="""
        Dict of `{'<lecture-code>': {members: list<str>, role: str}}`  to load at startup.

        Example::

            c.GraderService.load_roles = {
                'lecture1': {
                    'members': ['student1', 'student2'],
                    'role': 'student'
                    }
                },
                'lecture1': {
                    'members': ['instructor1', 'instructor2'],
                    'role': 'instructor'
                    }
                },
            }

        This will replace all existing roles.
        """,
    ).tag(config=True)

    oauth_clients = List(
        Dict(),
        default_value=[],
        help="""
        List of OAuth clients `[{'client_id': '<client_id>', 'client_secret': '<client_secret>', 'redirect_uri': '<redirect_uri>'}]` to register for the provider.
        
        Example::
            
            c.GraderService.oauth_clients = [{
                'client_id': 'hub',
                'client_secret': 'hub',
                'redirect_uri': 'http://localhost:8080/hub/oauth_callback'
            }]
    """,
    ).tag(config=True)

    @default("authenticator")
    def _authenticator_default(self):
        return self.authenticator_class(parent=self)

    @validate("config_file")
    def _validate_config_file(self, proposal):
        if not os.path.isfile(proposal.value) and not self.generate_config:
            print(
                "ERROR: Failed to find specified config file: {}".format(proposal.value),
                file=sys.stderr,
            )
            sys.exit(1)
        return proposal.value

    flags = {
        "debug": (
            {"Application": {"log_level": logging.DEBUG}},
            "Set log-level to debug, for the most verbose logging.",
        ),
        "show-config": (
            {"Application": {"show_config": True}},
            "Show the application's configuration (human-readable format)",
        ),
        "show-config-json": (
            {"Application": {"show_config_json": True}},
            "Show the application's configuration (json format)",
        ),
        "generate-config": (
            {"GraderService": {"generate_config": True}},
            "generate default config file",
        ),
    }

    aliases = {
        "log-level": "Application.log_level",
        "f": "GraderService.config_file",
        "config": "GraderService.config_file",
    }

    log_level = Enum(
        [
            0,
            10,
            20,
            30,
            40,
            50,
            "CRITICAL",
            "FATAL",
            "ERROR",
            "WARNING",
            "WARN",
            "INFO",
            "DEBUG",
            "NOTSET",
        ],
        "INFO",
    ).tag(config=True)

    def setup_loggers(self, log_level: str):  # pragma: no cover
        """Handles application, Tornado, and
        SQLAlchemy logging configuration."""
        stream_handler = logging.StreamHandler
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        fmt = "%(color)s%(levelname)-8s %(asctime)s %(module)-13s |%(end_color)s %(message)s"
        formatter = tornado.log.LogFormatter(fmt=fmt, color=True, datefmt=None)

        for log in ("access", "application", "general"):
            logger = logging.getLogger("tornado.{}".format(log))
            if len(logger.handlers) > 0:
                logger.removeHandler(logger.handlers[0])
            logger.setLevel(log_level)
            handler = stream_handler(stream=sys.stdout)
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        sql_logger = logging.getLogger("sqlalchemy")
        sql_logger.propagate = False
        sql_logger.setLevel("WARN")
        sql_handler = stream_handler(stream=sys.stdout)
        sql_handler.setLevel("WARN")
        sql_handler.setFormatter(formatter)
        sql_logger.addHandler(sql_handler)

        oauth_log = logging.getLogger("oauthlib")
        oauth_handler = stream_handler(stream=sys.stdout)
        oauth_handler.setFormatter(formatter)
        oauth_log.setLevel(log_level)
        oauth_log.addHandler(oauth_handler)

        traitlet_logger = traitlets_log.get_logger()
        traitlet_logger.removeHandler(traitlet_logger.handlers[0])
        traitlet_logger.setLevel(log_level)
        traitlets_handler = stream_handler(stream=sys.stdout)
        traitlets_handler.setFormatter(formatter)
        traitlet_logger.addHandler(traitlets_handler)

    def write_config_file(self):
        self.log.info(f"Writing config file {os.path.abspath(self.config_file)}")
        config_file_dir = os.path.dirname(os.path.abspath(self.config_file))
        if not os.path.isdir(config_file_dir):
            self.exit(
                f"The directory to write the config file has to exist. {config_file_dir} not found"
            )
        if os.path.isfile(os.path.abspath(self.config_file)):
            self.exit(
                f"Config file {os.path.abspath(self.config_file)} \
                already exists!"
            )

        members = inspect.getmembers(
            sys.modules[__name__], lambda x: inspect.isclass(x) and issubclass(x, HasTraits)
        )
        config_classes = [x[1] for x in members]

        config_text = self.generate_config_file(classes=config_classes)
        if isinstance(config_text, bytes):
            config_text = config_text.decode("utf8")
        print("Generating config: %s" % self.config_file)
        with open(self.config_file, mode="w") as f:
            f.write(config_text)

    def initialize(self, argv, *args, **kwargs):
        self.log.info("Starting Initialization...")
        self.log.info("Loading config file...")
        super().initialize(*args, **kwargs)
        self.parse_command_line(argv)
        self.load_config_file(self.config_file)
        self.setup_loggers(self.log_level)

        self.session_maker = get_session_maker(self.db_url)
        self.init_roles()
        # use uvloop instead of default asyncio loop
        # asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        self._start_future = asyncio.Future()

        if sys.version_info.major < 3 or sys.version_info.minor < 9:
            msg = "Grader Service needs Python version 3.9 or above to run!"
            raise RuntimeError(msg)
        if shutil.which("git") is None:
            msg = "No git executable found! Git is necessary to run Grader Service!"
            raise RuntimeError(msg)

    def set_config(self):
        """Pass config to singletons."""
        RequestHandlerConfig.config = self.config
        LTISyncGrades.config = self.config
        CeleryApp.instance(config=self.config)

    async def cleanup(self):
        pass

    def init_oauth(self):
        engine = create_engine(self.db_url)
        session = sessionmaker(engine)
        self.oauth_provider = make_provider(
            session,
            url_prefix=url_path_join(self.base_url_path, "api/oauth2"),
            login_url=url_path_join(self.base_url_path, "login"),
            token_expires_in=self.oauth_token_expires_in,
        )
        for client in self.oauth_clients:
            self.oauth_provider.add_client(
                client["client_id"], client["client_secret"], client["redirect_uri"], ["identify"]
            )

    def init_roles(self):
        """Load predefined groups into the database"""
        with self.session_maker() as db:
            users_loaded = set()
            for lecture_code, role_dict in self.load_roles.items():
                role = role_dict.get("role")
                users = role_dict.get("members", [])
                lecture = db.query(Lecture).filter(Lecture.code == lecture_code).one_or_none()
                # create lecture if no lecture with that name exists yet
                # (code is set in create)
                if lecture is None:
                    self.log.info(f"Adding new lecture with lecture_code {lecture_code}")
                    lecture = Lecture()
                    lecture.code = lecture_code
                    lecture.name = lecture_code
                    lecture.state = LectureState.active
                    lecture.deleted = DeleteState.active
                    db.add(lecture)
                db.commit()

                for username in users:
                    user = db.query(User).filter(User.name == username).one_or_none()
                    if user is None:
                        self.log.info(f"Adding new user with username {username}")
                        user = User()
                        user.name = username
                        user.display_name = username
                        db.add(user)
                        db.commit()

                    # delete all roles of users the first time a new role is added for the user
                    if user.name not in users_loaded:
                        db.query(Role).filter(Role.username == user.name).delete()
                        users_loaded.add(user.name)

                    try:
                        db.add(Role(username=user.name, lectid=lecture.id, role=Scope[role]))
                    except KeyError:
                        self.log.error(f"Invalid role name: {role}")
                        raise ValueError(f"Invalid role name: {role}")
                db.commit()

    async def start(self):
        self.log.info(f"Config File: {os.path.abspath(self.config_file)}")

        if self.generate_config:
            self.write_config_file()
            self.exit(0)

        self.log.info("Starting Grader Service...")
        self.io_loop = tornado.ioloop.IOLoop.current()

        self._setup_environment()

        self.init_oauth()

        # pass config
        self.set_config()

        handlers = HandlerPathRegistry.handler_list(self.base_url_path)
        self.log.info(handlers)
        # Add the handlers of the authenticator
        auth_handlers = self.authenticator.get_handlers(self.base_url_path)
        handlers.extend(auth_handlers)
        self.log.info(
            f"Registered authentication handlers for {self.authenticator.__class__.__name__}: {[n for n, _ in auth_handlers]}"
        )

        oauth_provider_handlers = oauth_handlers.get_oauth_default_handlers(self.base_url_path)
        handlers.extend(oauth_provider_handlers)
        self.log.info(f"Registered OAuth handlers: {[n for n, _ in oauth_provider_handlers]}")

        # start the webserver
        self.http_server: HTTPServer = HTTPServer(
            GraderServer(
                grader_service_dir=self.grader_service_dir,
                base_url=self.base_url_path,
                authenticator=self.authenticator,
                handlers=handlers,
                oauth_provider=self.oauth_provider,
                cookie_secret=self.grader_cookie_secret,  # generate new cookie secret at startup
                config=self.config,
                session_maker=self.session_maker,
                parent=self,
                login_url=self.authenticator.login_url(self.base_url_path),
                logout_url=self.authenticator.logout_url(self.base_url_path),
                static_url_prefix=url_path_join(self.base_url_path, "/static/"),
                static_handler_class=CacheControlStaticFilesHandler,
                log_function=log_request,
            ),
            # ssl_options=ssl_context,
            max_buffer_size=self.max_buffer_size,
            max_body_size=self.max_body_size,
            xheaders=True,
        )
        self.log.info(f"Service directory - {self.grader_service_dir}")
        self.http_server.listen(
            self.service_port, address=self.service_host, reuse_port=self.reuse_port
        )

        for s in (signal.SIGTERM, signal.SIGINT):
            asyncio.get_event_loop().add_signal_handler(
                s, lambda: asyncio.ensure_future(self.shutdown_cancel_tasks(s))
            )

        self.log.info(f"Grader service running at {self.service_host}:{self.service_port}")

        # finish start
        self._start_future.set_result(None)

    def _setup_environment(self):
        if not os.path.exists(os.path.join(self.grader_service_dir, "git")):
            os.mkdir(os.path.join(self.grader_service_dir, "git"))
        # check if git config exits so that git commits don't fail
        if (
            subprocess.run(
                ["git", "config", "init.defaultBranch"], check=False, capture_output=True
            )
            .stdout.decode()
            .strip()
            != "main"
        ):
            raise RuntimeError("Git default branch has to be set to 'main'!")
        if (
            subprocess.run(["git", "config", "user.name"], check=False, capture_output=True)
            .stdout.decode()
            .strip()
            == ""
        ):
            raise RuntimeError("Git user.name has to be set!")
        if (
            subprocess.run(["git", "config", "user.email"], check=False, capture_output=True)
            .stdout.decode()
            .strip()
            == ""
        ):
            raise RuntimeError("Git user.email has to be set!")

    async def shutdown_cancel_tasks(self, sig):
        """Cancel all other tasks of the event loop and initiate cleanup"""
        self.log.critical("Received signal %s, initiating shutdown...", sig.name)

        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

        if tasks:
            self.log.debug("Cancelling pending tasks")
            [t.cancel() for t in tasks]

            try:
                await asyncio.wait(tasks)
            except asyncio.CancelledError:
                self.log.debug("Caught Task CancelledError. Ignoring")
            except StopAsyncIteration:
                msg = "Caught StopAsyncIteration Exception"
                self.log.error(msg, exc_info=True)

            tasks = [t for t in asyncio.all_tasks()]
            for t in tasks:
                self.log.debug("Task status: %s", t)
        await self.cleanup()
        asyncio.get_event_loop().stop()

    async def launch_instance_async(self, argv=None):
        try:
            self.initialize(argv)
            await self.start()
        except Exception as e:
            self.log.exception(e)
            self.exit(1)

    @classmethod
    def launch_instance(cls, argv=None):
        self = cls.instance()
        loop = tornado.ioloop.IOLoop.current()
        task = asyncio.ensure_future(self.launch_instance_async(argv))
        try:
            loop.start()
        except KeyboardInterrupt:
            print("\nInterrupted")
        finally:
            if task.done():
                # re-raise exceptions in launch_instance_async
                task.result()
            loop.stop()

    @validate("grader_service_dir")
    def _validate_service_dir(self, proposal):
        path: str = proposal["value"]
        if not os.path.isabs(path):
            raise TraitError("The path is not absolute")
        if not os.path.isdir(path):
            os.mkdir(path, mode=0o700)
        return path

    @observe("grader_service_dir")
    def _observe_service_dir(self, change):
        path = change["new"]
        git_path = os.path.join(path, "git")
        if not os.path.isdir(git_path):
            os.mkdir(git_path, mode=0o700)
