#!/bin/bash

echo "Creating virtual environment..."
python -m venv venv
source ./venv/bin/activate
which python

python -m pip install --upgrade pip
pip install jupyterhub jupyterlab

echo "Installing grader_service..."
cd ../../
pip install -e .

echo "Installing grader_labextension..."
cd ../Grader-Labextension
pip install -e .

jupyter labextension develop . --overwrite

jupyter server extension enable grader_labextension

# verify installation
jupyter server extension list
jupyter labextension list

# home directory for users
mkdir -p ./home_dir

mkdir -p ./service_dir
chmod 777 ./service_dir

# create db in grader service directory
cd service_dir || exit
grader-service-migrate
cd .. || exit

mkdir -p ./service_dir/git
chmod 777 ./service_dir/git

pip list

deactivate 