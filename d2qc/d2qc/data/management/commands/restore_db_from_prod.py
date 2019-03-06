# Restore the database from the production environment

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from d2qc.setup.tools import postgres_wo_password
from datetime import datetime
import os
import logging
import sys

class Command(BaseCommand):
    '''Restore the database from the production environment. You need to have
    your ssh-key added to the production-server for this to work. In addition,
    you might need to make the following changes to ~/.ssh/config
    Host                    *
      ForwardAgent          yes
    '''

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--migrate',
            action='store_true',
            help='Apply existing migrations after restoring',
        )

    def handle(self, *args, **options):
        '''Restore the database
        '''
        # Logger for handling errors
        logger = logging.getLogger(__name__)

        db_name = settings.DATABASES['default']['NAME']
        user = settings.DATABASES['default']['USER']
        pw = settings.DATABASES['default']['PASSWORD']
        host = settings.DATABASES['default']['HOST']
        port = settings.DATABASES['default']['PORT']
        ip = settings.PROD_SERVER_IP
        remote_db_file = settings.PROD_SERVER_DB_FILE
        remote_data_folder = os.path.join(
            settings.PROD_SERVER_USER_DATA_FOLDER,
            ''
        )
        data_folder = settings.DATA_FOLDER
        backup_folder = settings.BACKUP_FOLDER
        backup_db_file = os.path.join(
            backup_folder,
            os.path.basename(remote_db_file)
        )

        # check ssh connection
        if 0 != os.system(
                "ssh -o StrictHostKeyChecking=no -q ubuntu@{} exit".format(ip)
        ):
            logger.error("Could not connect to server {}. Exiting.".format(ip))
            sys.exit()

        verbose = ''
        if options['verbosity'] > 0:
            verbose = '-v'

        # Get data files
        cmd = "rsync -zrt {} --delete ".format(verbose)
        cmd += "ubuntu@{}:{} {}".format(ip, remote_data_folder, data_folder)
        if options['verbosity'] > 0:
            self.stdout.write(self.style.SUCCESS(cmd))
        os.system(cmd)

        # Get db backup file
        if os.path.islink(backup_db_file):
            os.remove(backup_db_file)

        cmd = "rsync -ztLk {} ".format(verbose)
        cmd += "ubuntu@{}:{} {}".format(ip, remote_db_file, backup_folder)
        if options['verbosity'] > 0:
            self.stdout.write(self.style.SUCCESS(cmd))
        os.system(cmd)

        # restore database from backup
        cmd = "pg_restore --clean --if-exists --schema public "
        cmd += "{} --dbname {} --host {} --username {} ".format(
            verbose,
            db_name,
            host,
            user
        )
        cmd += backup_db_file

        postgres_wo_password()
        if options['verbosity'] > 0:
            self.stdout.write(self.style.SUCCESS(cmd))
        os.system(cmd)
        if options['migrate']:
            call_command('migrate', verbosity=options['verbosity'])

