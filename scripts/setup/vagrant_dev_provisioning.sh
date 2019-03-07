#####################################################################
# Development only
#
# This provisioning script is only run if environment
# variable DEV is true
#
#####################################################################

cd /vagrant
source .env_vagrant/bin/activate
cd d2qc
python manage.py add_dev_admin_user
