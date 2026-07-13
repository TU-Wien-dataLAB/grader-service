# Package Installation

```{note}
This setup is intended for **local development and testing purposes only**.
It is **not suitable for production use**. Use the [Kubernetes installation](../kubernetes) for production deployments.
```

This guide explains how to install the published `grader-service` backend and `grader-labextension` frontend packages from [PyPI](https://pypi.org) into your own environment. If you want to run from source instead, see the [Quick installation](quick_install) or [Installation from source](installation_from_source) guides.

---

## Requirements

- Python 3.9+
- JupyterHub >= 5.x ([installation guide](https://jupyterhub.readthedocs.io/en/stable/tutorial/quickstart.html))
- JupyterLab >= 4.x ([installation guide](https://jupyterlab.readthedocs.io/en/latest/getting_started/installation.html))

## Create a virtual environment

### Using `venv`:

```bash
python -m venv grader
source grader/bin/activate
```

### Using `uv`:

```bash
uv venv grader
source grader/bin/activate
```

### Using `conda`:

```bash
conda create -n grader python=3.1x
conda activate grader
```

## 1. Install `grader-service` (Python Backend)

```bash
pip install grader-service
```

Or with `uv`:

```bash
uv pip install grader-service
```

## 2. Install `grader-labextension` (JupyterLab Frontend)

```bash
pip install grader-labextension
```

Or with `uv`:

```bash
uv pip install grader-labextension
```

Installing the labextension registers the JupyterLab frontend and the server extension automatically; no manual `jupyter labextension develop` / `jupyter server extension enable` steps are required.

## 3. Configuration of Grader Service

Generate a default configuration file:

```bash
grader-service --generate-config
```

Alternatively, use the example configuration files from the `dev/local/token/` directory in the repository.

Run the migration to create the database:

```bash
grader-service-migrate -f <config-file-path>/grader_service_config.py
```

## 4. Start Grader Service and JupyterHub

First start the `grader-service`:

```bash
grader-service -f <config-file-path>/grader_service_config.py
```

Then launch JupyterHub:

```bash
jupyterhub -f <config-file-path>/jupyterhub_config.py
```

## Optional: Cleanup

To uninstall all components:

```bash
pip uninstall grader-service grader-labextension
```
