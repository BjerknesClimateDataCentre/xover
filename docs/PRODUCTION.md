
Production setup information
----------------------------

Production setup depends on your requirements and your preferred system. The
vagrant setup includes a minimal setup using apache as a web server.

To configure the production system:

`cp d2qc/d2qc/setup/sample.production.py d2qc/d2qc/setup/production.py`

And update `production.py` with correct details. For

To make sure the production.py setup is used for shell scripts on the
server, make sure the following environment variable is set:

`export DJANGO_SETTINGS_MODULE=d2qc.setup.production`

Restart apache for the changes to take effect:
`sudo service apache2 restart`

Access the system on http://localhost:8081.
