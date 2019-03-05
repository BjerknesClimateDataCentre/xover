# Make standard mariadb backup of the database

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from datetime import datetime
import os

class Command(BaseCommand):

    def handle(self, *args, **options):
        '''Make a backup of the database
        '''

        db_name = settings.DATABASES['default']['NAME']
        user = settings.DATABASES['default']['USER']
        pw = settings.DATABASES['default']['PASSWORD']
        host = settings.DATABASES['default']['HOST']
        port = settings.DATABASES['default']['PORT']
        _file = settings.BACKUP_FOLDER
        if not os.path.isdir(_file):
            os.makedirs(_file)
        pgpass_file = os.path.expanduser('~/.pgpass')
        if not os.path.isfile(pgpass_file):
            with open(pgpass_file, 'a') as pgpass:
                pgpass.write("{}:{}:{}:{}:{}".format(
                        host, port or '*', user, pw, db_name
                    )
                )
            os.chmod(pgpass_file, 0o600)

        _file += '/d2qc-dbbackup-'
        _file += datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        _file += '.dump'
        cmd = "pg_dump "
        cmd += "--file {} ".format(_file)
        cmd += "--username {} ".format(user)
        cmd += "--host {} ".format(host)
        if port:
            cmd += "--port {} ".format(port)
        cmd += "--compress 9 --format c "
        cmd += "d2qc"
        os.system(cmd)
        latest = settings.BACKUP_FOLDER + "/latest.dump"
        os.remove(latest)
        os.symlink(_file, latest)
