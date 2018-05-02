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
WSGIScriptAlias / /vagrant/d2qc/d2qc/wsgi.py
WSGIPythonHome /vagrant/.env_vagrant
WSGIPythonPath /vagrant/d2qc

<Directory /vagrant/d2qc/d2qc>
<Files wsgi.py>
Require all granted
</Files>
</Directory>
EOF
echo "$apache" > /etc/apache2/conf-available/wsgi.conf

a2enconf wsgi
service apache2 reload
