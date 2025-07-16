# Kubernetes

## Prerequisites

- Kubernetes cluster
- kubectl installed and configured
- Helm installed and repsitory added:
    - [Install Helm](https://helm.sh/docs/intro/install/)
    - [Add the Helm repository](https://helm.sh/docs/intro/quickstart/#add-a-helm-repository)
    ```bash
    helm repo add grader-service ghcr.io/tu-wien-datalab/grader-service
    ```

## Install Grader Service
If you already have a JupyterHub installation, you can also install only the Grader Service using Helm:
```bash
helm upgrade --install <your-release-name> grader-service \
    --namespace <your-namespace> \
    --create-namespace \
    --values <your-values.yaml>
```

## Test Installation (All-in-One)
To test the system, we provide an all-in-one Helm chart that includes both the Grader Service and a configured JupyterHub instance. It is suitable **for development and testing purposes only**.
```bash
helm upgrade --install <your-release-name> grader-service-all-in-one \
    --namespace <your-namespace> \
    --create-namespace \
    --values <your-values.yaml>
```

