
Shortcuts and aliases
---------------------

On the vagrant machine (after `vagrant up; vagrant ssh`):

* Activate the correct python environment and setup in the current terminal:
  * `a` alias for `source /vagrant/.env_vagrant/bin/activate` # Run from any folder
* `manage.py` is the Django script for running scripts etc bootstrapped with
    the Django environment.
  * `m` alias for `./manage.py` # Run from /vagrant/d2qc
* Start the Django development server:
  * `dev` alias for `./manage.py runserver 0.0.0.0:8000` # From /vagrant/d2qc
