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
admin,b=User.objects.get_or_create(username='admin')
admin.is_superuser = True
admin.is_staff = True
admin.set_password('123')
admin.email = 'jhe052@uib.no'
admin.save()
" | python manage.py shell
