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
  git submodule update
fi
# Add Virtualenv install folder to path:
echo 'PATH="$PATH:/home/vagrant/.local/bin"' >> ~/.profile
source ~/.profile

# Install Virtualenv
python -m pip install --user virtualenv


if [ ! -d .env_vagrant ]
then
#  virtualenv -p python3 --no-site-packages --distribute .env_vagrant
  virtualenv -p python3 --no-site-packages .env_vagrant
fi

source .env_vagrant/bin/activate


# Upgrade pip
pip install --upgrade pip

# Initialize pip with requirements
pip install -r scripts/setup/requirements.txt

# Shortcuts:
echo "alias a='source .env_vagrant/bin/activate'" >> ~/.profile
echo "alias m='python manage.py'" >> ~/.profile
source ~/.profile

# Run django migrations
cd d2qc
python manage.py migrate
