# Package Installation


```{note}
This setup is intended for **local development and testing purposes only**.
It is **not suitable for production use**. Use the [Kubernetes installation](../kubernetes) for production deployments.
```

This guide explains how to locally install and run the `grader-service` backend and the `grader-labextension` frontend.

---

## Requirements

- Python 3.9+
- pip
- JupyterHub >= 3.x ([installation guide](https://jupyterhub.readthedocs.io/en/stable/tutorial/quickstart.html))
- JupyterLab >= 3.x ([installation guide](https://jupyterlab.readthedocs.io/en/latest/getting_started/installation.html))
<!---
0. create python env (optional)
1. install grader-service
   1. pip install grader-service
   2. create config (--generate-config)
   3. create database (grader-service-migrate -f config_file)
   4. start grader-service (grader-service -f config_file)
2. install grader-labextension
   1.pip install
3. jupyterhub
   1. create config
   2. start jupyterhub
--->

## Create a virtual environment (Optional)
### Using `venv`:
```
python -m venv grader
```
Activate the environment:
```
source grader/bin/activate
```
### Using `conda`:
```
conda create -n grader python=3.1x.x
```
Activate the environment:
```
conda activate grader
```

## 1. Install `grader-service` (Python Backend)

<h4>
Install the Python package and its dependencies:
</h4>

```bash
pip install grader-service
```

---

## 2. Install `grader-labextension` (JupyterLab Frontend)

Run the following command:

```bash
pip install grader-labextension
```

## 3. Configuration of Grader Service

Generate a default configuration file:

```bash
grader-service --generate-config
```

Or use the example configuration files from `dev/local/` directory in the repository.

Run the migration to create the database:

```bash
grader-service-migrate -f <config-file-path>/grader_service_config.py
```


## 4. Start Grader Service and JupyterHub
First start the `grader-service`:
```bash
grader-service -f <config-file-path>/grader_service_config.py
```
Then launch the JupyterHub:
```bash
jupyterhub -f <config-file-path>/jupyterhub_config.py
```

## Optional: Cleanup

To uninstall all components:

```
pip uninstall grader-service jupyterlab
pip uninstall grader-labextension
```
