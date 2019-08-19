from django.conf import settings
from django.core.management.base import CommandError
from d2qc.data.management.newline_command import NewlineCommand
from d2qc.setup.tools import postgres_wo_password
from datetime import datetime
import os

class Command(NewlineCommand):
    help = """
        Make a backup of the database. This function uses the current
        setup to make a database dump in the backup folder also specified in
        the configuration. Backup files are in the postgres dump format. They
        are named: d2qc-dbbackup-YYYY-mm-dd_HH:MM:SS.dump
        There is also a softlink called latest.dump, pointing to the last
        generated backup.
    """


    def handle(self, *args, **options):

        db_name = settings.DATABASES['default']['NAME']
        user = settings.DATABASES['default']['USER']
        pw = settings.DATABASES['default']['PASSWORD']
        host = settings.DATABASES['default']['HOST']
        port = settings.DATABASES['default']['PORT']
        _file = settings.BACKUP_FOLDER
        if not os.path.isdir(_file):
            os.makedirs(_file)

        postgres_wo_password()

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
        if os.path.isfile(latest):
            os.remove(latest)
        os.symlink(_file, latest)
