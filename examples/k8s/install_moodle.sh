#!/usr/bin/env bash

helm upgrade --cleanup-on-fail \
  --install grader-moodle bitnami/moodle \
  --namespace jupyter \
  --create-namespace \
  --values moodle-config.yaml
