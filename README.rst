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
===========

.. TODO: is this still correct?

..

   JupyterHub,
   JupyterLab,
   Python >= 3.8,
   pip,
   Node.js>=12,
   npm

Installation
============

.. installation-start

This repository contains the packages for the jupyter extensions and the grader service itself.

The grader service has only been tested on Unix/macOS operating systems.

This repository contains all the necessary packages for a full installation of the grader service.


* ``grader-service``\ : Manages students and instructors, files, grading and multiple lectures. It can be run as a standalone containerized service and can utilize a kubernetes cluster for grading assignments. This package also contains ``grader-convert``, a tool for converting notebooks to different formats (e.g. removing solution code, executing, etc.). It can be used as a command line tool but will mainly be called by the service. The conversion logic is based on `nbgrader <https://github.com/jupyter/nbgrader>`_.

.. code-block::

    pip install grader-service

* ``grader-labextension``\ : The JupyterLab plugin for interacting with the service. Provides the UI for instructors and students and manages the local git repositories for the assignments and so on. The package is located in its `own repo <https://github.com/TU-Wien-dataLAB/Grader-Labextension>`_.

.. code-block::

    pip install grader-labextension



.. installation-end

.. installation-from-soruce-start

Installation from Source
--------------------------

To install this package from source, clone into the repository or download the `zip file <https://github.com/TU-Wien-dataLAB/Grader-Service/archive/refs/heads/main.zip/>`_.

Local installation
^^^^^^^^^^^^^^^^^^^^

In the ``grader`` directory run:

.. code-block:: bash

   pip install -r ./grader_labextension/requirements.txt
   pip install ./grader_labextension

   pip install -r ./grader_service/requirements.txt
   pip install ./grader_service


Then, navigate to the ``grader_labextension``\ -directory and follow the instructions in the README file.

Development Environment
^^^^^^^^^^^^^^^^^^^^^^^^

Alternatively you can run the installation scripts in ``examples/dev_environment``.
Follow the documentation there. The directory also contains the config files for a local installation.

.. installation-from-soruce-end


Getting Started
===============

.. TODO: completely outdated -> refer to config in dev environment instead + clean up configs there (only minimal config with lots of comments)
                what is confusing about configs? write comments!
                what parts can be omitted? should we set default values explicitly?
                describe --show-config command -> does this even work?


.. running-start

Grader service uses RabbitMQ as a task broker to delegate grading tasks to separate worker instances.
Please follow their `tutorials <https://www.rabbitmq.com/docs/download>`_ on how to set up and run a RabbitMQ server on your host machine.
Our `helm` chart automatically deploys a RabbitMQ cluster when installing the grader service through the `RabbitMQ Kubernetes Operator <https://www.rabbitmq.com/docs/kubernetes/operator/operator-overview>`_.

Running grader service
--------------------------

To run the grader service you first have to register the service in JupyterHub as an unmanaged service in the config:

.. code-block:: python

    c.JupyterHub.services.append(
        {
            'name': 'grader',
            'url': 'http://127.0.0.1:4010',
            'api_token': '<token>'
        }
    )

The api token can be generated in the jupyterhub control panel.
You can verify the config by running ``jupyterhub -f <config_file.py>`` and you should see the following error message: ::

    Cannot connect to external service grader at http://127.0.0.1:4010. Is it running?

Specifying user roles
--------------------------

Since the JupyterHub is the only source of authentication for the service, it has to rely on the JupyterHub to provide all the necessary information for user groups.

Users have to be added to specific groups which maps the users to lectures and roles. They have to be separated by colons.

The config could look like this:

.. code-block:: python

    ## generic
    c.JupyterHub.admin_access = True
    c.Spawner.default_url = '/lab'
    c.Spawner.cmd=["jupyter-labhub"]


    ## authenticator
    c.JupyterHub.authenticator_class = 'jupyterhub.auth.DummyAuthenticator'
    c.Authenticator.allowed_users = {'user1', 'user2', 'user3', 'user4'}
    c.Authenticator.admin_users = {'user1', 'user2', 'user3', 'user4'}

    ## spawner
    c.JupyterHub.spawner_class = 'jupyterhub.spawner.SimpleLocalProcessSpawner'
    c.SimpleLocalProcessSpawner.home_dir_template = '/path/to/lab_dir/{username}'


    c.JupyterHub.load_groups = {
        "lect1:instructor": {'users': ["user1"]},
        "lect1:tutor": {'users': ["user2"]},
        "lect1:student": {'users': ["user3", "user4"]},
    }

Here, ``user1`` is an instructor of the lecture with the code ``lect1`` and so on.

Starting the service
--------------------------

In order to start the grader service we have to provide a configuration file for it as well:

.. code-block:: python

    import os

    c.GraderService.service_host = "127.0.0.1"
    # existing directory to use as the base directory for the grader service
    service_dir = os.path.expanduser("<grader_service_dir>")
    c.GraderService.grader_service_dir = service_dir

    c.JupyterHubGroupAuthenticator.hub_api_url = "http://127.0.0.1:8081/hub/api"

    c.LocalAutogradeExecutor.relative_input_path = "convert_in"
    c.LocalAutogradeExecutor.relative_output_path = "convert_out"


The ``<token>`` has to be the same value as the JupyterHub service token specified earlier. The ``grader_service_dir`` directory has to be an existing directory with appropriate permissions to let the grader service read and write from it.

Alternatively, you can run ``grader-service --generate-config -f /path/to/grader_service_config.py`` to generate the skeleton for the config file that show all possible configuration options.

Furthermore the database must be initialized before we can start the service.
To do this navigate to the ``grader_service_dir`` that was specified and execute the following command: ::

    grader-service-migrate

Then the grader service can be started by specifying the config file as such: ::

    grader-service -f <grader_service_config.py>

When restarting the JupyterHub you should now see the following log message: ::

    Adding external service grader at http://127.0.0.1:4010

Do not forget to set the log level to ``INFO`` in the JupyterHub config if you want to see this message.

The last thing we have to configure is the server-side of the JupyterLab plugin which also needs information where to access the endpoints of the service. This can be done in the ``jupyter_server_config.py`` file. When using the defaults from above we do not need to explicitly configure this but it would look like this:

.. code-block:: python

    import os
    c.GitService.git_access_token = os.environ.get("JUPYTERHUB_API_TOKEN")
    c.GitService.git_remote_url = "http://127.0.0.1:4010/services/grader/git"

    c.RequestService.url = "http://127.0.0.1:4010"


.. running-end

Using LTI3 Authenticator
=========================

In order to use the grader service with an LMS like Moodle, the groups first have to be added to the JupyterHub so the grader service gets the necessary information from the hub.

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

* ``Run Cell``: This command simply run the current cell without advancing.

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
