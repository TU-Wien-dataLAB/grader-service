# Local Installation

```{note}
This setup is intended for **local development and testing purposes only**.  
It is **not suitable for production use**.
```

This guide explains how to locally install and run the `grader-service` backend and the `grader-labextension` frontend.

---

## Requirements

- Python 3.8+
- pip
- JupyterHub >= 3.x
- JupyterLab >= 3.x


## 1. Install `grader-service` (Python Backend)

Ensure you have **Python 3.8+** and **pip** installed.

```
pip install grader-service
```

This installs the `grader-service` Python package and its dependencies.

To start the service locally:

```
grader-service
```

```{tip}
You may need to provide configuration options such as the port or config file, depending on your setup.
```

---

## 2. Install `grader-labextension` (JupyterLab Frontend)

Make sure **JupyterLab** is installed:

```
pip install jupyterlab
```

Then install the grader lab extension:

```
pip install grader-labextension
```

To launch JupyterLab:

```
jupyter lab
```

After launching, the grader extension should be visible in the JupyterLab interface.

---

## 3. Testing the Setup

- Open **JupyterLab** in your browser.
- Access the grader interface from the sidebar or launcher.
- Ensure the frontend can communicate with the `grader-service` backend.

---

## Optional: Cleanup

To uninstall all components:

```
pip uninstall grader-service jupyterlab
pip uninstall grader-labextension
```

---

