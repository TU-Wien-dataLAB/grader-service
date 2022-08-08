
Prerequisites
^^^^^^^^^^^^^^^^^^^^
Before installing the Grader Service you will
need:

- Python 3.7 or greater.
- Node.js 10.8 or greater.

Installing Jupyterhub and Jupyterlab
^^^^
Jupyterhub can be installed with ``pip`` or ``conda``

.. code-block::
    pip install jupyterhub
    pip install jupyterlab

Local Installation
^^^
Firstly clone the Grader Service repository to your computer.
Navigate to the ``grader`` directory and install the packages:

.. code-block::

   pip install -r ./grader_convert/requirements.txt
   pip install --no-use-pep517 ./grader_convert

   pip install -r ./grader_labextension/requirements.txt
   pip install ./grader_labextension

   pip install -r ./grader_service/requirements.txt
   pip install --no-use-pep517 ./grader_service


Then, navigate to the ``grader_labextension``\ -directory and follow the instructions in the README file.

### after installation of npm, nginx and conda
# install jupyterhub and grader service, incl. prerequisites

# create dir for jupyter user spawning
mkdir ~/jupyter-test

# create conda env
conda create -n grader python=3.9 pip
conda activate grader

# install jupyterhub jupyterlab locally
pip install jupyterhub jupyterlab
# create jupyter config file
# jupyterhub_config.py

# install yarn if not there
sudo npm install --global yarn
export PATH=$PATH:/usr/local/lib/node_modules/yarn/bin/

#install grader
# download and unzip grader source
# cd to unpacked grader installation dir.
pip install -r ./grader_convert/requirements.txt
pip install --no-use-pep517 ./grader_convert
pip install -r ./grader_labextension/requirements.txt
pip install ./grader_labextension
pip install -r ./grader_service/requirements.txt
pip install --no-use-pep517  ./grader_service

# create grader config file
#  grader_service_config.py

# migrate grader service
grader-service-migrate
alembic -c /home/jokke/Downloads/Grader-Service-main/grader_service/grader_service/migrate/alembic.ini upgrade head

# install lab extension
pip install grader_labextension

# start jupyterhub and grader (in separate terminals)
jupyterhub -f jupyterhub_config.py
grader-service -f grader_service_config.py