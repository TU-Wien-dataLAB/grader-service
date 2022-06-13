Local Development Environment
################################

The directory contains bash scripts to setup a local environment in this directory and servers
as a guide for more complex setups. The bash scripts have to be run in the ``dev_environment`` directory.

It contains four bash files:

* ``install.sh``: Sets up a virtual environment in the directory and install the necessary dependencies. Also creates the directories for the grader service.
* ``run_hub.sh``: Start a JupyterHub instance with the config provided in ``jupyter_hub_config.py``.
* ``run_service.py``: Start a grader service instance with the config provided in ``grader_service_config.py``.
* ``clean.sh``: Cleans up the directories created in ``install.sh`` and other auxiliary files. Does not delete the virtual environment.
