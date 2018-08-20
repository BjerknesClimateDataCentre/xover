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
echo "
from django.contrib.auth import get_user_model;
User = get_user_model();
User.objects.create_superuser('admin', 'jhe052@uib.no', '123');" \
    | python manage.py shell
