# Quick installation

## Installation Scripts

For a quick installation you can use installation scripts which you can find in `examples/dev_environment` directory. 
This directory provides you with local development environment and serves as a guide for more complex setups.
Ensure that you cloned the [Grader Labextension project](https://github.com/TU-Wien-dataLAB/grader-labextension) and it is located in the same directory as the grader
service repository.

The `dev_enviroment` directory contains following files:

- `install.sh`: Sets up a virtual environment in the directory and installs the necessary dependencies. Also creates the directories for the grader service.
- `run_hub.sh`: Start a JupyterHub instance with the config provided in `jupyter_hub_config.py`.
- `run_service.sh`: Start a grader service instance with the config provided in `grader_service_config.py`.
- `clean.sh`: Cleans up the directories created in `install.sh` and other auxiliary files. Does not delete the virtual environment.

## Installation

To install Grader Service and Grader Labextension navigate to directory `example/dev_environment`. Start installation script by running command:

```bash
bash ./install.sh
```

Installation script creates a virtual environment and adds all needed packages to it.

## Start Grader Service and JupyterHub
To start Grader Service run following command line:

```bash
bash ./run_service.sh
```

Grader Service runs at `http://127.0.0.1:4010`.

To start JupyterHub and connect it to Grader Service, run:

```bash
bash ./run_hub.sh
```

JupyterHub instance will be running at `http://127.0.0.1:8080`.

```{note}
First the Grader Service must be started, then the JupyterHub.
```
