#!/bin/bash

################################################################################
#
# Script to setup python and django dev env for vagrant environment
# This script is run by a user with full sudo privileges.
#
################################################################################

# Go to the dev folder
cd /vagrant

# Apache configuration:
read -r -d '' apache <<'EOF'
WSGIDaemonProcess django2qc python-home=/vagrant/.env_vagrant python-path=/vagrant/d2qc
WSGIProcessGroup django2qc
WSGIScriptAlias / /vagrant/d2qc/d2qc/wsgi.py process-group=django2qc

<Directory /vagrant/d2qc/d2qc>
<Files wsgi.py>
Require all granted
</Files>
</Directory>
EOF
echo "$apache" > /etc/apache2/conf-available/wsgi.conf

a2enconf wsgi
service apache2 reload
