#!/usr/bin/env bash

helm repo add jupyterhub https://jupyterhub.github.io/helm-chart/
helm repo update

helm upgrade --install ingress-nginx ingress-nginx \
  --repo https://kubernetes.github.io/ingress-nginx \
  --namespace ingress-nginx --create-namespace

echo "Waiting for the ingress-nginx-controller service to be available..."

kubectl wait --namespace ingress-nginx \
  --for=condition=Ready \
  pod -l app.kubernetes.io/name=ingress-nginx \
  --timeout=300s

if [ $? -ne 0 ]; then
    echo "Timed out waiting for the ingress-nginx-controller service to be available."
    exit 1
fi

echo "Ingress NGINX deployment completed successfully."

helm upgrade --cleanup-on-fail \
  --install my-jupyterhub jupyterhub/jupyterhub \
  --namespace jupyter \
  --create-namespace \
  --version=3.2.1 \
  --values hub-config.yaml
  