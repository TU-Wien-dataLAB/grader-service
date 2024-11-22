#!/usr/bin/env bash

helm uninstall -n jupyter my-grader
helm uninstall -n jupyter my-jupyterhub
helm uninstall -n jupyter grader-db
helm uninstall -n ingress-nginx ingress-nginx
