#!/bin/bash

echo "Creating virtual environment..."
python -m venv venv
source ./venv/bin/activate
which python

python -m pip install --upgrade pip
pip install jupyterhub jupyterlab

echo "Installing grader_convert..."
pip install -r ../../grader_convert/requirements.txt
pip install -e ../../grader_convert

echo "Installing grader_service..."
pip install -r ../../grader_service/requirements.txt
pip install -e ../../grader_service
grader-service-migrate

echo "Installing grader_labextension..."
pip install -r ../../grader_labextension/requirements.txt
pip install ../../grader_labextension # no development install for grader_labextension

jupyter server extension enable grader_labextension

# verify installation
jupyter server extension list
jupyter labextension list

# home directory for users
mkdir -p ./home_dir

mkdir -p ./service_dir
chmod 777 ./service_dir

mkdir -p ./service_dir/git
chmod 777 ./service_dir/git

pip list

deactivate