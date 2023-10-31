#/usr/bin/env bash

helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

helm upgrade --cleanup-on-fail \
  --install grader-db bitnami/postgresql \
  --namespace jupyter \
  --create-namespace \
  --values postgresql-config.yaml
