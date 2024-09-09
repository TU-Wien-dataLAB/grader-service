# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

# Python script that will apply the migrations up to head
import argparse
import alembic.config
import os
import re

here = os.path.dirname(os.path.abspath(__file__))

alembic_args = [
    '-c', os.path.join(here, 'alembic.ini'),
    'upgrade', 'head'
]


def getargs():
    "Give the option of passing args on the commandline"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", "-f", action='store',
                        default=None,
                        help="Path to grader service config")
    return parser.parse_args()


def load_custom_config(config):
    """Load a custom config file that uses the same format as Juypterhub and
    GraderService"""
    from grader_service.main import GraderService
    service = GraderService.instance()
    service.load_config_file(config)
    service.set_config()
    db_url = service.db_url
    if db_url is None:  # no match, do nothing
        return
    environment = {}
    environment.update({
        "GRADER_DB_URL": db_url,
    })
    # use environment to set global env vars
    os.environ.update(environment)


def main():
    args = getargs()
    if args.config:
        load_custom_config(args.config)
    alembic.config.main(argv=alembic_args)


if __name__ == '__main__':
    main()
