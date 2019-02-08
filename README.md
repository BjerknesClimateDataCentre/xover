

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
  * `git clone git@github.com:jonasfh/xover.git`
3. `cd xover`
4. The project has a couple of submodules. To fetch these, run:
  * `git submodule init`
  * `git submodule update`
5. There is an extra development provisioning script to automatically create an
   admin user during provisioning, with user admin, password 123. Set an
   environment variable DEV=true for this to run on vagrant up:
  * `export DEV=true`
4. `cp d2qc/d2qc/setup/sample.development.py d2qc/d2qc/setup/development.py`
  * Update `development.py` with correct details
 5. `vagrant up`

This spins up an ubuntu virtual machine using vagrant and virutalbox. The
project root folder is linked up on the vagrant machine as /vagrant.

Consider uncommenting the LOGGING - section in development.py. This will enable
logging of SQL statements, and is useful during development, but bothersom when
lots of data is loaded.

Vagrant / Django development setup functionality
----------------------------------------------

The setup includes Django with setup and services to ease the development
process. Frequently used commands are added as aliases on the vagrant box:

### Aliases ###
* Activate the correct python environment and setup in the current terminal:
  * `a` alias for `source /vagrant/.env_vagrant/bin/activate` # Run from any folder
* `manage.py` is the Django script for running scripts etc bootstrapped with
    the Django environment.
  * `m` alias for `./manage.py` # Run from /vagrant/d2qc
* Start the Django development server:
  * `dev` alias for `./manage.py runserver 0.0.0.0:8000` # From /vagrant/d2qc

### Development server ###
To use the Django development server on the vagrant machine:

1. Log in to the dev server
  * `vagrant ssh`
3. Activate the virtual python environment for the terminal
  * `source /vagrant/.env_vagrant/bin/activate`
4. Start the Django development server
  * `cd /vagrant/d2qc # project folder`
  * `./manage.py runserver 0.0.0.0:8000`
5. Access the dev server on http://localhost:8001
6. PS: You need to keep the terminal running with the server
7. To import some reference data, run
  * `./manage.py import_testdata `

Set up a testserver
-------------------

To set up a standalone test-server using UH-IAAS, follow instructions
[here](docs/setup_testserver.py).

Production setup information
----------------------------
Production setup depends on your requirements and your preferred system. The
vagrant setup includes a minimal setup using apache as a web server.

To configure the production system:

`cp d2qc/d2qc/setup/sample.production.py d2qc/d2qc/setup/production.py`

And update `production.py` with correct details. For

Restart apache for the changes to take effect:
`sudo service apache2 restart`

Access the system on http://localhost:8081.


Accessing the services
----------------------

The service supports using the standard Django admin interface for managing
data. This is accessed at http://localhost:8001/admin (`localhost:8001` is just the
dev server, and could be different for you). To set up a superuser
for the admin interface can be done using `python manage.py createsuperuser`
on the command line when in the d2qc/ folder.

API access is found at the /data - endpoint. Adding format=json as
GET - attributes returns raw pure json, otherwise data is presented in a
human readable format, using Django rest frameworks standard setup.

The API is still experimental, but currently supports

Get join data set:
    http://localhost:8001/data/join/dataset/{data_set_id}/[original_label,original_label,...]
    Example: http://localhost:8001/data/join/dataset/724/CTDTMP,SALNTY

Return data on the form:

    {
        expocode: "74DI20110715",
        id: 724,
        data_columns: [
            "id",
            "latitude",
            "longitude",
            "depth",
            "unix_time_millis",
            "CTDTMP_value",
            "SALNTY_value"
        ],
        data_points: [
            [
                1541950,
                48.6499,
                -17.0256,
                604,
                1311078240,
                8.8719,
                35.345
            ],
            [
                1541951,
                48.6499,
                -17.0256,
                604,
                1311078240,
                8.8763,
                35.3438
            ],
            ...
        ]
    }
