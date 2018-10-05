# Make standard mariadb backup of the database

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from datetime import datetime
import os

class Command(BaseCommand):

    def handle(self, *args, **options):
        # Make a backup of the database

        db_name = settings.DATABASES['default']['NAME']
        user = settings.DATABASES['default']['USER']
        pw = settings.DATABASES['default']['PASSWORD']
        host = settings.DATABASES['default']['HOST']
        port = settings.DATABASES['default']['PORT']
        file = settings.BACKUP_FOLDER
        if not os.path.isdir(file):
            os.makedirs(file)

        file += '/d2qc-dbbackup-'
        file += datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        file += '.sql'
        cmd = "mysqldump --default-character-set=UTF8 "
        cmd += "--user={} --password={} ".format(user, pw)
        cmd += "--host={} --port={} ".format(host, port)
        cmd += "{} ".format(db_name)
        cmd += " | gzip - > '{}.gz' ".format(file)
        os.system(cmd)
