# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

# Python script that will apply the migrations up to head
import alembic.config
import os

here = os.path.dirname(os.path.abspath(__file__))

alembic_args = [
    '-c', os.path.join(here, 'alembic.ini'),
    'upgrade', 'head'
]


def main():
    alembic.config.main(argv=alembic_args)
