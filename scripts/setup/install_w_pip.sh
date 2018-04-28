#!/bin/bash

################################################################################
#
# Install Django and other packages with pip
#
# To save the current setup in the requirements file, run: 
# pip freeze >requirements.txt
#
################################################################################
git clone https://github.com/django/django.git
pip install -r requirements.txt
