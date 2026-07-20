.. image:: ./docs/source/_static/assets/images/logo_name.png
   :width: 95%
   :alt: banner
   :align: center

General

.. image:: https://readthedocs.org/projects/grader-service/badge/?version=latest
    :target: https://grader-service.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://img.shields.io/github/license/TU-Wien-dataLAB/Grader-Service
    :target: https://github.com/TU-Wien-dataLAB/Grader-Service/blob/main/LICENSE
    :alt: BSD-3-Clause

.. image:: https://img.shields.io/github/commit-activity/m/TU-Wien-dataLAB/Grader-Service
    :target: https://github.com/TU-Wien-dataLAB/Grader-Service/commits/
    :alt: GitHub commit activity




Grader Service

.. image:: https://img.shields.io/pypi/v/grader-service
    :target: https://pypi.org/project/grader-service/
    :alt: PyPI

.. image:: https://img.shields.io/pypi/pyversions/grader-service
    :target: https://pypi.org/project/grader-service/
    :alt: PyPI - Python Version



Grader Labextension

.. image:: https://img.shields.io/pypi/v/grader-labextension
    :target: https://pypi.org/project/grader-labextension/
    :alt: PyPI

.. image:: https://img.shields.io/pypi/pyversions/grader-labextension
    :target: https://pypi.org/project/grader-labextension/
    :alt: PyPI - Python Version

.. image:: https://img.shields.io/npm/v/grader-labextension
    :target: https://www.npmjs.com/package/grader-labextension
    :alt: npm



**Disclaimer**: *Grader Service is still in the early development stages. You may encounter issues while using the service.*

Grader Service offers lecturers and students a well integrated teaching environment for data science, machine learning and programming classes.

Try out GraderService:

.. TODO: update binder

.. image:: https://mybinder.org/badge_logo.svg
    :target: https://mybinder.org/v2/gh/TU-Wien-dataLAB/grader-demo/HEAD?urlpath=lab
    :alt: binder


Read the `official documentation <https://grader-service.readthedocs.io/en/latest/index.html>`_.

.. image:: ./docs/source/_static/assets/gifs/labextension_update.gif

Requirements
============

* Python >= 3.9
* `JupyterHub <https://jupyterhub.readthedocs.io/en/stable/tutorial/quickstart.html>`_ >= 5.x
* `JupyterLab <https://jupyterlab.readthedocs.io/en/latest/getting_started/installation.html>`_ >= 4.x
* pip

Building the labextension frontend from source additionally requires Node.js >= 20 and ``npm``.

Installation
============

.. installation-start

The grader service has only been tested on Unix/macOS operating systems.


* ``grader-service``\ : Manages students and instructors, files, grading and multiple lectures. It can be run as a standalone containerized service and can utilize a kubernetes cluster for grading assignments. This package also contains ``grader-convert``, a tool for converting notebooks to different formats (e.g. removing solution code, executing, etc.). It can be used as a command line tool but will mainly be called by the service. The conversion logic is based on `nbgrader <https://github.com/jupyter/nbgrader>`_.

.. code-block::

    pip install grader-service

* ``grader-labextension``\ : The JupyterLab plugin for interacting with the service. Provides the UI for instructors and students and manages the local git repositories for the assignments and so on. The source is part of this repository under ``packages/labextension``.

.. code-block::

    pip install grader-labextension


.. installation-from-soruce-end

.. installation-from-soruce-start

Installation from Source
^^^^^^^^^^^^^^^^^^^^^^^^

The repository is a `uv workspace <https://docs.astral.sh/uv/concepts/projects/workspaces/>`_ monorepo, so a single command installs both ``grader-service`` and ``grader-labextension`` in editable mode together with all development, test, and documentation dependencies.

Prerequisites: Python >= 3.9, `uv <https://docs.astral.sh/uv/>`_, Node.js >= 20, Git.

Clone the repository:

.. code-block:: bash

   git clone https://github.com/TU-Wien-dataLAB/grader-service.git
   cd packages/grader-service

Install all packages:

.. code-block:: bash

   make sync

This runs ``uv sync --all-packages --all-groups`` and creates a single virtual environment with both packages installed. Because the repository is configured as a uv workspace, the labextension's dependency on ``grader-service`` is resolved from the local package.

Create the database schema by running the migration against a service config (example configs are provided in ``dev/local/token/``):

.. code-block:: bash

   uv run grader-service-migrate -f dev/local/token/grader_service_config.py

Start the grader service, then JupyterHub:

.. code-block:: bash

   make run-service
   make run-hub

The labextension frontend is installed in editable mode; rebuild it after TypeScript changes with ``jlpm build`` (run from ``packages/labextension``) or use ``make watch-labextension`` to rebuild on every change.

For the full list of development commands, see ``DEVELOPMENT.md``.

.. installation-from-soruce-end

Development Environment
^^^^^^^^^^^^^^^^^^^^^^^^

A fully containerized development stack (Grader Service, JupyterHub, RabbitMQ, Celery worker, and SQLite database) is provided in ``dev/docker-compose``:

.. code-block:: bash

   make dev-up

JupyterHub will be running at ``http://127.0.0.1:8080``. Stop the stack with ``make dev-down``.

A standalone Docker Compose example (without the monorepo build tooling) is available under ``examples/docker_compose``.

Configuration
===============
Check out the ``dev/docker-compose`` directory (or the example config files in ``dev/local/token``) or the `Administrator Guide <https://grader-service.readthedocs.io/en/latest/admin/administrator.html>`_.

In order to use the grader service with an LMS like Moodle, the groups first have to be added to the JupyterHub so the Grader Service gets the necessary information from the hub.

For this purpose, the `LTI 1.3 Authenticator <https://github.com/TU-Wien-dataLAB/lti13oauthenticator>`_ can be used so that users from the LMS can be added to the JupyterHub.

To automatically add the groups for the grader service from the LTI authenticator, the following `post auth hook <https://jupyterhub.readthedocs.io/en/stable/api/auth.html#jupyterhub.auth.Authenticator.post_auth_hook>`_ can be used.

.. code-block:: python

    from jupyterhub import orm
    import sqlalchemy

    def post_auth_hook(authenticator, handler, authentication):
        db: sqlalchemy.orm.session.Session = authenticator.db
        log = authenticator.log

        course_id = authentication["auth_state"]["course_id"].replace(" ","")
        user_role = authentication["auth_state"]["user_role"]
        user_name = authentication["name"]

        # there are only Learner and Instructors
        if user_role == "Learner":
            user_role = "student"
        elif user_role == "Instructor":
            user_role = "instructor"
        user_model: orm.User = orm.User.find(db, user_name)
        if user_model is None:
            user_model = orm.User()
            user_model.name = user_name
            user_model.display_name = user_name
            db.add(user_model)
            db.commit()

        group_name = f"{course_id}:{user_role}"
        group = orm.Group.find(db, group_name)
        if group is None:
            log.info(f"Creating group: '{group_name}'")
            group = orm.Group()
            group.name = group_name
            db.add(group)
            db.commit()

        extra_grader_groups = [g for g in user_model.groups if g.name.startswith(f"{course_id}:") and g.name != group_name]
        for g in extra_grader_groups:
            log.info(f"Removing user from group: {g.name}")
            g.users.remove(user_model)
            db.commit()

        if user_model not in group.users:
            log.info(f"Adding user to group: {group.name}")
            group.users.append(user_model)
            db.commit()

        return authentication


Make sure that the ``course_id`` does not contain any spaces or special characters!

Optional Configuration of JupyterLab >=3.4
==========================================

The grader labextension also uses the embedded cell toolbar of JupyterLab for further cell manipulation.
These optional features include:

* ``Run Cell``: This command simply runs the current cell without advancing.

* ``Revert Cell``: In the conversion process new metadata is set to allow students to revert every answer cell to their original state.

* ``Show Hint``: Students can access a hint to a task if one is specified.

To access these commands buttons have to be added to the JupyterLab cell toolbar by editing the `overrides.json file <https://jupyterlab.readthedocs.io/en/stable/user/directories.html#overridesjson>`_.
We also recommend that all other built in cell toolbar buttons should be disabled in the config because they might enable unwanted cell manipulation by students.

A sample overrides.json file could look like this:

.. code-block:: json

    {
        "@jupyterlab/cell-toolbar-extension:plugin": {
            "toolbar": [
                {
                    "args": {},
                    "command": "notebookplugin:run-cell",
                    "disabled": false,
                    "rank": 501,
                    "name": "run-cell"
                },
                {
                    "args": {},
                    "command": "notebookplugin:revert-cell",
                    "disabled": false,
                    "rank": 502,
                    "name": "revert-cell"
                },
                {
                    "args": {},
                    "command": "notebookplugin:show-hint",
                    "disabled": false,
                    "rank": 503,
                    "name": "show-hint"
                }
            ]
        }
    }
