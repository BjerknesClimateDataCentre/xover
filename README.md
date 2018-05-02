

2QC Matlab to Python
====================

The aim of this software is to provide an online tool for making similar
corrections to data, as the 2QC matlab - library does.

Development setup information
-----------------------------

The server software is written in Python with the Django framework. The easiest
way to get started is to use the Vagrant setup:

1. Install Vagrant on your machine
  * (https://www.vagrantup.com/intro/getting-started/)
2. Checkout the project
  * git clone git@git.app.uib.no:Jonas.Henriksen/django2qc.git
3. `cd django2qc`
4. vagrant up

This should start up a new instance of an Ubuntu server. You can access the
system on http://localhost:8081

To use the django development server:

1. Log in to the dev server
  * `vagrant ssh`
2. `cd /vagrant`
3. Activate the virtual python environment
  * `./env_vagrant/bin/activate`
  * `a` is an alias for the above
4. Start development server
  * `d2qc/manage.py runserver 0.0.0.0:8000`
5. Access the dev server on http://localhost:8001
6. PS: You need to keep the terminal running with the server
