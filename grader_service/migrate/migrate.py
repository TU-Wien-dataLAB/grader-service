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


def get_config_file(cfile):
    with open(cfile, 'r') as f:
        lines = f.read()
    return lines


def get_matching_config(text, patt: re.Pattern):
    """Load a config value by matching a line in text that contains pattern 
    Assume the line contains a 'key = value' type of pair, split the line at 
    equals and return the value part.
    """
    lines = text.split('\n')
    result = None
    for line in lines: 
        match = re.match(patt, line)
        if match:
           _, db_url, _ = match.groups()
           result = db_url
    return result 


DB_URL_PATT = re.compile(r"(c.GraderService.db_url = ')(.*?)(')")

def load_custom_config(cfile):
    """Load a custom config file that uses the same format as Juypterhub and
    GraderService"""
    global DB_URL_PATT
    db_url = get_matching_config(cfile, DB_URL_PATT)
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
        cfile = get_config_file(args.config)
        load_custom_config(cfile)
    alembic.config.main(argv=alembic_args)
