#!/usr/bin/env bash

# install the rabbit-mq operator
kubectl apply -f "https://github.com/rabbitmq/cluster-operator/releases/latest/download/cluster-operator.yml"

# install grader
bash install_postgresql.sh
bash install_grader.sh
bash install_ingress_nginx.sh
bash install_hub.sh