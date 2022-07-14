#/usr/bin/env bash

helm repo add grader-service https://tu-wien-datalab.github.io/Grader-Service
helm repo update

helm upgrade --cleanup-on-fail \
  --install my-grader grader-service/grader-service \
  --namespace jupyter \
  --create-namespace \
  --values grader-config.yaml

# INSTALL LOCAL GRADER CHART:

#helm upgrade --cleanup-on-fail \
#  --install my-grader ../../charts/grader-service \
#  --namespace jupyter \
#  --create-namespace \
#  --values grader-config.yaml
