# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import enum
import os

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base

from grader_service.api.models.base_model import Model

Base = declarative_base()

database_type = os.getenv("DATABASE_TYPE")
if database_type == "sqlite":
    # The following function is needed to enable foreign key constraints in SQLite;
    # The code was copied from the SQLAlchemy documentation:
    # https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#foreign-key-support
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        # the sqlite3 driver will not set PRAGMA foreign_keys
        # if autocommit=False; set to True temporarily
        ac = dbapi_connection.autocommit
        dbapi_connection.autocommit = True

        cursor = dbapi_connection.cursor()
        # Note: this is a SQLite-specific pragma
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

        # restore previous autocommit setting
        dbapi_connection.autocommit = ac


class Serializable(object):
    @property
    def model(self) -> Model:
        return Model()

    def serialize(self) -> dict:
        return self.model.to_dict()


class DeleteState(enum.IntEnum):
    active = 0
    deleted = 1
