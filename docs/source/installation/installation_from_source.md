# Grader Service and Grader Labextension Installation from Source


## Installation Requirements

Before installing the Grader Service, make sure that following packages are installed on your machine:

```bash
 # Python is needed for all packages
    
Python >= 3.10
    
 # For running Grader Labextension you will need:
JuypterHub
JupyterLab
pip 
Node.js
npm
```

## Local Installation

### Grader Service

To locally install Grader Service, make sure to clone [this project](https://github.com/TU-Wien-dataLAB/Grader-Service) on your machine or download the [zip file](https://github.com/TU-Wien-dataLAB/Grader-Service/archive/refs/heads/main.zip).

Once you have your local copy of Grader Service repository navigate to `Grader-Service` directory and run:

```python
pip install -e .
```

Running this command will make sure that all dependencies from `pyproject.toml` file are installed and that Grader-Service is ready to run.

### Grader Labextension

To locally install Grader Labextension, make sure to clone [Grader Labextension project](https://github.com/TU-Wien-dataLAB/grader-labextension) or download the corresponding [zip file](https://github.com/TU-Wien-dataLAB/Grader-Labextension/archive/refs/heads/main.zip).

Grader Labextension is composed of a Python package named `grader_labextension` for the server extension and an NPM package `grader-labextension` for the frontend extensio.

To install the extension in development mode, navigate to your local `grader-labextension` directory and run:

```bash
pip install -e .
```

Link your development version of the extension with JupyterLab:

```bash
jupyter labextension develop . --overwrite
```

Python server extension (`grader_labextension`) must be manually installed in development mode:

```bash
jupyter server extension enable grader_labextension
```

After making changes in Labextension, extension's Typescript source has to be rebuilt in order for you to see the changes. This can be done using the `jlpm` command, which is JupyterLab's pinned version of [yarn](https://yarnpkg.com/) and is installed alongside JupyterLab. To rebuild extension you may use `yarn` or `npm` instead of `jlpm` which is shown in the example below.

```bash
jlpm build
```

To observe changes immediately, without a need to manually rebuild the TypeScript source files, you can open a separate terminal alongside terminal in which Grader Labextension is running and there you can run:

```bash
# Watch the source directory and automatically rebuild the extension
jlpm watch
```

The `jlpm watch` command monitors changes in the extension's source code and automatically rebuilds the extension whenever a change is detected. With the watch command running, every saved change is immediately built and made available in your running JupyterLab. You only need to refresh JupyterLab to load the changes in your browser. Note that it may take several seconds for the extension to rebuild.

Keep in mind that `jlpm watch` continues running until you stop it and can consume significant system resources. Therefore, it may sometimes be better to manually rebuild the TypeScript source using `jlpm build`.

## Installation Scripts

Alternatively you can use installation scripts which you can find in `examples/dev_environment` directory. This directory provides you with local development environment and serves as a guide for more complex setups. The bash scripts have to be run in the `dev_environment` directory.
Ensure that you cloned the [Grader Labextension project](https://github.com/TU-Wien-dataLAB/grader-labextension) and it is located in the same directory as the grader service repository.

The `dev_enviroment` directory contains following files:

-  `install.sh`: Sets up a virtual environment in the directory and install the necessary dependencies. Also creates the directories for the grader service.
-  `run_hub.sh`: Start a JupyterHub instance with the config provided in `jupyter_hub_config.p`y.
- `run_service.sh`: Start a grader service instance with the config provided in `grader_service_config.py`.
- `clean.sh`: Cleans up the directories created in `install.sh` and other auxiliary files. Does not delete the virtual environment.

To install Grader Service and Grader Labextension navigate to directory `example/dev_environment`. Start installation script by running command:

```bash
bash ./install.sh
```

Installation script creates a virtual environment and adds all needed packages to it.

To start Grader Service run following command line:

```bash
bash ./run_service.sh

```

Grader Service runs at `http://127.0.0.1:4010`.

To start JupyterHub and connect it to Grader Service, run:

```bash
bash ./run_hub.sh
```

JupyterHub instance will be running at `http://localhost:8080`.

First Grader Service must be started, than JupyterHub.

