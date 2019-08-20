
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

* [Developing with Django / Vagrant](DJANGO.md)

Vagrant / Django development setup functionality
----------------------------------------------

The setup includes Django with setup and services to ease the development
process. Frequently used commands are added as aliases on the vagrant box:
