#!/bin/bash

################################################################################
#
# Script to setup python and django dev env for vagrant environment
# This script is run by the unpriviledged user.
#
################################################################################

# Go to the dev folder
cd /vagrant

# get django repo if not exists
if [ ! -d django ]
then
  # Django is cloned from https://github.com/django/django.git
  git submodule init
  gti submodule update
fi

python -m pip install --user virtualenv


if [ ! -d .env_vagrant ]
then
#  virtualenv -p python3 --no-site-packages --distribute .env_vagrant
  virtualenv -p python3 --no-site-packages .env_vagrant
fi

source .env_vagrant/bin/activate


# Initialize pip with requirements
pip install -r scripts/setup/requirements.txt

# Activate shortcut:
echo "alias a='source .env_vagrant/bin/activate'" >> ~/.profile
source ~/.profile
