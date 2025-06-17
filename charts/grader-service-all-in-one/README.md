# Grader Service All-in-One Chart
> **_NOTE:_**  This chart should be used for development and testing purposes only. It is not recommended for production use, as it use dummy authentication by default.

This chart deploys the Grader Service along with a configured JupyterHub in a single Helm chart.

## Configuration
The chart has two top-level configuration options:
- `grader-service`: Configuration for the `grader-service` chart.
- `jupyterhub`: Configuration for the Zero to JupyterHub chart ([Z2JH Docs](https://z2jh.jupyter.org/en/stable/)).