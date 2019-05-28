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
        initdb_path = settings.INITDB_PATH
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
        cmd = "rsync -zrt {} --delete ".format(
            verbose if options['verbosity']>1 else ''
        )
        cmd += "ubuntu@{}:{} {}".format(ip, remote_data_folder, data_folder)
        if options['verbosity'] > 0:
            self.stdout.write(self.style.SUCCESS(cmd))
        os.system(cmd)

        # Get db backup file
        if os.path.islink(backup_db_file):
            os.remove(backup_db_file)

        cmd = "rsync -ztLk {} ".format(
            verbose if options['verbosity']>1 else ''
        )
        cmd += "ubuntu@{}:{} {}".format(ip, remote_db_file, backup_folder)
        if options['verbosity'] > 0:
            self.stdout.write(self.style.SUCCESS(cmd))
        os.system(cmd)

        # Terminate all connections:
        sql = """
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '"'"'{}'"'"'
            AND pid <> pg_backend_pid();
        """.format(db_name)
        os.system(
            "sudo -u postgres sh -c 'psql {} -c \"{}\"'".format(db_name, sql)
        )

        # drop the current database
        os.system("sudo -u postgres dropdb {}".format(db_name))

        # re-create database
        os.system(
            "sudo -u postgres createdb -O {} {}".format(user, db_name)
        )

        # Initalize database (install postgis etc)
        with open(initdb_path, 'r') as file:
            sql = file.read()
        os.system(
            "sudo -u postgres sh -c 'psql {} -c \"{}\"'".format(db_name, sql)
        )

        # restore database from backup
        cmd = "pg_restore --schema public "
        cmd += "{} --dbname {} --host {} --username {} ".format(
            verbose if options['verbosity']>1 else '',
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
