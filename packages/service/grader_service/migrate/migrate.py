# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

# Python script that will apply the migrations up to head
import argparse
import logging
import os
import re
from urllib.parse import urlparse, urlunparse

import alembic.config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to the directory containing this script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Alembic command arguments
alembic_args = ["-c", os.path.join(script_dir, "alembic.ini"), "upgrade", "head"]


def redact_db_url(url):
    """Redact sensitive parts of the database URL for logging."""
    parsed_url = urlparse(url)
    netloc = parsed_url.netloc

    if "@" in netloc:
        userinfo, hostinfo = netloc.split("@", 1)
        username = re.sub(r":.*$", "", userinfo)  # Extract username
        netloc = f"{username}:REDACTED@{hostinfo}"

    redacted_url = urlunparse(
        (
            parsed_url.scheme,
            netloc,
            parsed_url.path,
            parsed_url.params,
            parsed_url.query,
            parsed_url.fragment,
        )
    )
    return redacted_url


def get_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Apply Alembic migrations up to head.")
    parser.add_argument("--config", "-f", default=None, help="Path to custom config file")
    return parser.parse_args()


def load_custom_config(config_path):
    """Load and apply configuration from a custom file."""
    from grader_service.main import GraderService

    try:
        service = GraderService.instance()
        service.load_config_file(config_path)
        service.set_config()
        db_url = service.db_url
        logger.info(f"Database URL: {redact_db_url(db_url)}")

        if db_url:
            os.environ["GRADER_DB_URL"] = db_url
        else:
            logger.info("No db_url configuration found, using default db_url")
    except Exception as e:
        logger.error(f"Failed to load custom config: {e}")
        raise


def main():
    args = get_args()
    if args.config:
        load_custom_config(args.config)

    try:
        alembic.config.main(argv=alembic_args)
    except SystemExit as e:
        logger.error(f"Migration failed: {e}")
        raise


if __name__ == "__main__":
    main()
