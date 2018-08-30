

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
5. `cp d2qc/d2qc/setup/sample.production.py d2qc/d2qc/setup/production.py`
  * Update `production.py` with correct details

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


Accessing the services
----------------------

The service supports using the standard django admin interface for managing
data. This is accessed at http://localhost:8001/admin (`localhost:8001` is just the
dev server, and could be different for you). To set up a superuser
for the admin interface can be done using `python manage.py createsuperuser`
on the command line when in the d2qc/ folder.

API access is found at the /data - endpoint. Adding format=json as
GET - attributes returns raw pure json, otherwise data is presented in a
human readable format, using django rest frameworks standard setup.

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
