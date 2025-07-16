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
   Python >= 3.9,
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


.. installation-from-soruce-end

.. installation-from-soruce-start

Installation from Source
^^^^^^^^^^^^^^^^^^^^

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

Configuration
===============
Check out the ``examples/dev_environment`` directory which contains configuration details or the `Administrator Guide <https://grader-service.readthedocs.io/en/latest/admin/administrator.html>`_.

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
