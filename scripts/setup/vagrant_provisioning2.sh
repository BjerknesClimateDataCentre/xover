#!/bin/bash

################################################################################
#
# Script to setup python and django dev env for vagrant environment
# This script is run by the unpriviledged user.
#
################################################################################

# Go to the dev folder
cd /vagrant

# get submodule repositories if not present
git submodule init
git submodule update

# Add Virtualenv install folder to path:
echo 'PATH="$PATH:/home/vagrant/.local/bin"' >> ~/.profile
source ~/.profile

# Remove possibly existing environment folder
rm -rf .env_vagrant
python3 -m venv .env_vagrant

source .env_vagrant/bin/activate


# Upgrade pip
pip install --upgrade pip

# Initialize pip with requirements
pip install -r scripts/setup/requirements.txt

# Install basemap separately
pip install https://github.com/matplotlib/basemap/archive/v1.1.0.tar.gz

# Set backend to default Agg by commenting line
sed -i 's/^\( *backend *:.*\)$/# \1/' \
    /vagrant/.env_vagrant/lib/python3.*/site-packages/matplotlib/mpl-data/matplotlibrc

# Shortcuts:
echo "alias a='source /vagrant/.env_vagrant/bin/activate'" >> ~/.profile
echo "alias m='python manage.py'" >> ~/.profile
echo "alias dev='python manage.py runserver 0.0.0.0:8000'" >> ~/.profile
source ~/.profile

# Check django configs exist
if [ ! -e d2qc/d2qc/setup/development.py ]
then
  cp d2qc/d2qc/setup/sample.development.py d2qc/d2qc/setup/development.py
  echo "Copying d2qc/d2qc/setup/sample.development.py to development.py"
  echo "Modify this file if needed"
fi

if [ ! -e d2qc/d2qc/setup/production.py ]
then
  cp d2qc/d2qc/setup/sample.production.py d2qc/d2qc/setup/production.py
  echo "Copying d2qc/d2qc/setup/sample.production.py to production.py"
  echo "Modify this file if needed"
fi

# Run django migrations
cd d2qc
python manage.py restore_db_from_prod --verbosity 1
python manage.py migrate
