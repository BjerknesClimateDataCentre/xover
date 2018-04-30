#!/bin/bash

################################################################################
#
# Script to setup python and django dev env for vagrant environment
# This script is run by a user with full sudo privileges.
#
################################################################################

# Go to the dev folder
cd /vagrant

apt-get update

# Database setup
apt-get install -y mariadb-server

echo "CREATE USER 'd2qc'@'localhost';" |mysql -uroot
echo "GRANT ALL PRIVILEGES ON d2qc.* To 'd2qc'@'localhost' IDENTIFIED BY 'd2qc';" \
    |mysql -uroot
echo "CREATE DATABASE d2qc CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" \
    |mysql -uroot

# Install Python, pip, virtualenv
apt-get install -y python-pip
apt-get install -y python-dev
apt-get install -y libmysqlclient-dev
apt-get install -y python3-dev

# Upgrade pip to latest version
pip install --upgrade pip
