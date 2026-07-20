# Kubernetes

## Prerequisites

- Kubernetes cluster
- kubectl installed and configured
- Helm installed (>= 3.8 for OCI support):
    - [Install Helm](https://helm.sh/docs/intro/install/)
    - The chart is distributed as an OCI artifact from the GitHub Container Registry at `oci://ghcr.io/tu-wien-datalab/grader-service/charts`.
- [RabbitMQ operator](https://www.rabbitmq.com/kubernetes/operator/install-operator#installation) installed

## Install Grader Service
If you already have a JupyterHub installation, you can also install only the Grader Service using Helm:
```bash
helm upgrade --install <your-release-name> \
    oci://ghcr.io/tu-wien-datalab/grader-service/charts/grader-service \
    --namespace <your-namespace> \
    --create-namespace \
    --version <chart-version> \
    --values <your-values.yaml>
```

To configure the Grader Service to connect to your existing JupyterHub, you need to set the appropriate values in your `values.yaml` file, such as the JupyterHub API URL and authentication credentials.
You can find the necessary configuration options in our [configuration documentation](../configuration/index.md).

## Test Installation (All-in-One)
To test the system, we provide an all-in-one Helm chart that includes both the Grader Service and a configured JupyterHub instance. It is suitable **for development and testing purposes only**.

:::{note}
The `grader-service-all-in-one` Helm chart can be found in the `charts/` directory.
:::
```bash
helm upgrade --install <your-release-name> <path-to-chart> \
    --namespace <your-namespace> \
    --create-namespace \
    --values <your-values.yaml>
```
