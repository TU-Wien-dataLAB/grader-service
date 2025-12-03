# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import enum

from sqlalchemy.orm import declarative_base

from grader_service.api.models.base_model import Model

Base = declarative_base()


class Serializable(object):
    @property
    def model(self) -> Model:
        return Model()

    def serialize(self) -> dict:
        return self.model.to_dict()


class DeleteState(enum.IntEnum):
    active = 0
    deleted = 1
