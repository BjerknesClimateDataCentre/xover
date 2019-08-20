
Django development server
-----------------------------

* Based on the [development setup section](SETUP.md)

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
