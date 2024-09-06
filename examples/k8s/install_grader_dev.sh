#!/usr/bin/env bash

helm upgrade --cleanup-on-fail \
  --install my-grader ../../charts/grader-service \
  --namespace jupyter \
  --create-namespace \
  --values grader-config.yaml
