#!/bin/bash

################################################################################
#
# Install Django and other packages with pip
#
# make sure you have installed python and pip
# (These are platform dependent)
# apt install python
# Pip:
# apt install python-pip
# Upgrade Pip:
# pip install --upgrade pip
# Virtualenv:
# pip install virtualenv
#
# To save the current setup in the requirements file, run:
# pip freeze >requirements.txt
#
################################################################################
if [ -z "$(which pip)" ]
then
  echo "pip is not installed. Please install pip to continue."
  exit
fi
pip install --upgrade pip
if [ -z "$(which virtualenv)" ]
then
  pip install virtualenv
fi

if [ ! -d .env ]
then
  virtualenv -p python3 --no-site-packages --distribute .env
fi

if [[ -z "$VIRTUAL_ENV" ]]
then
    source .env/bin/activate
fi
if [ ! -d django ]
then
  git clone https://github.com/django/django.git
fi

pip install -r scripts/setup/requirements.txt

