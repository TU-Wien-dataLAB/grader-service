Local Development Environment
################################

The directory contains bash scripts to setup a local environment in this directory and servers
as a guide for more complex setups. The bash scripts have to be run in the ``dev_environment`` directory.

It contains four bash files:

* ``install.sh``: Sets up a virtual environment in the directory and install the necessary dependencies. Also creates the directories for the grader service.
* ``run_hub.sh``: Start a JupyterHub instance with the config provided in ``jupyter_hub_config.py``.
* ``run_service.sh``: Start a grader service instance with the config provided in ``grader_service_config.py``.
* ``clean.sh``: Cleans up the directories created in ``install.sh`` and other auxiliary files. Does not delete the virtual environment.

In order to install Grader Service navigate to folder ``examples/dev_environment``. Make sure to run installation script by running command line ``bash ./install.sh``.
Installation script creates a virtual enviroment and installs all needed packages in it.

To start JuypterHub, run ``bash ./run_hub.sh`` in the command line. JupyterHub instance will be running at ``http://localhost:8080``.

To connect JupyterHub to Grader Service open a separate terminal and run following command line:  ``bash ./run_service.sh``. Once shell script was run, Grader Service automatically connects to Jupyterhub.
Grader Service runs at ``http://127.0.0.1:4010``.