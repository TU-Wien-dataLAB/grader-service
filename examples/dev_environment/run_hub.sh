#!/bin/bash
source ./venv/bin/activate

export JUPYTERHUB_CRYPT_KEY=$(openssl rand -hex 32)
jupyterhub -f ./jupyterhub_config.py
