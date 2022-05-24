# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

from pathlib import Path

from setuptools import find_packages
from setuptools import setup
import os
from grader_service.main import main
from grader_service.alembic.migrate import main as migrate_main
from grader_service._version import __version__

source_root = Path(__file__).parent
# Read the requirements
with (source_root / "requirements.txt").open(encoding="utf8") as f:
    requirements = f.readlines()

setup(
    name='grader-service',
    version=__version__,
    packages=find_packages(".", exclude=["grader_service.tests", "grader_service.tests.*"]),
    package_data={'grader_service.alembic': ['alembic.ini']},
    url="https://github.com/TU-Wien-dataLAB/Grader-Service",
    license="BSD-3-Clause",
    author='Elias Wimmer, Florian Jäger & Matthias Matt',
    author_email='',
    description='Grader service',
    entry_points={
        'console_scripts': [
            f'grader-service = {main.__module__}:main',
            f'grader-service-migrate = {migrate_main.__module__}:main'
        ],
    },
    python_requires=">=3.8",
    install_requires=requirements,
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Development Status :: 3 - Alpha",
        "Framework :: Jupyter",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
