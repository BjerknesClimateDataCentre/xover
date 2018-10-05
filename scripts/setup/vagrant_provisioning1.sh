#!/bin/bash

################################################################################
#
# Script to setup python and django dev env for vagrant environment
# This script is run by a user with full sudo privileges.
#
################################################################################

# Go to the dev folder
cd /vagrant

# Prevent errors trying to access stdin
export DEBIAN_FRONTEND=noninteractive

add-apt-repository -y ppa:ubuntugis/ppa
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

# Install postgresql database server
apt-get install -y binutils libproj-dev gdal-bin python-gdal
apt-get install -y postgresql postgresql-contrib libpq-dev
apt-get install -y postgresql-client postgresql-client-common
sudo -u postgres  sh -c 'psql -c "CREATE USER d2qc WITH PASSWORD '"'"'d2qc'"'"';"'
sudo -u postgres  sh -c 'psql -c "ALTER ROLE d2qc SET client_encoding TO '"'"'utf8'"'"';"'
sudo -u postgres  sh -c 'psql -c "ALTER ROLE d2qc SET default_transaction_isolation TO '"'"'read committed'"'"';"'
sudo -u postgres  sh -c 'psql -c "ALTER ROLE d2qc SET timezone TO '"'"'UTC'"'"';"'
sudo -u postgres createdb -O d2qc d2qc

# Install postgis extensions
apt-get install -y postgis
sudo -u postgres  sh -c 'psql d2qc -c "CREATE EXTENSION postgis;"'



# Install Python, pip, virtualenv
apt-get install -y python-pip
apt-get install -y python-dev
apt-get install -y libmysqlclient-dev
apt-get install -y python3-dev
apt-get install -y python3-tk

# Install GEOS for matplotlib
apt-get install -y libgeos-c1v5 libgeos-dev


# Install apache and mod_wsgi
apt-get install -y apache2 apache2-utils libexpat1 ssl-cert
apt-get install libapache2-mod-wsgi-py3
service apache2 restart

# Upgrade pip to latest version
pip install --upgrade pip
