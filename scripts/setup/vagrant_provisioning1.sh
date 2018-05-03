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
apt-get upgrade -y

# Database setup
apt-get install -y mariadb-server
echo "SET GLOBAL sql_mode='STRICT_ALL_TABLES'" |mysql -uroot
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

# Install apache and mod_wsgi
apt-get install -y apache2 apache2-utils libexpat1 ssl-cert
apt-get install libapache2-mod-wsgi-py3
service apache2 restart

# Upgrade pip to latest version
pip install --upgrade pip
