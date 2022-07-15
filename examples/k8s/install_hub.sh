#/usr/bin/env bash

helm repo add jupyterhub https://jupyterhub.github.io/helm-chart/
helm repo update

latest_version=$(curl -s https://jupyterhub.github.io/helm-chart/info.json | jq -r '.jupyterhub.latest' )

helm upgrade --cleanup-on-fail \
  --install my-jupyterhub jupyterhub/jupyterhub \
  --namespace jupyter \
  --create-namespace \
  --version=$latest_version \
  --values hub-config.yaml
  