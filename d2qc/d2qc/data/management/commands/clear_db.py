from django.conf import settings
from d2qc.data.management.newline_command import NewlineCommand
from django.core.management import call_command
import os
import logging
import sys

class Command(NewlineCommand):
    help = """
        Drop and recreate the database, optionally migrate to the current
        pristine state.

        -m / --migrate  Migrate database to current version. Also adding
                        cache table
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '-m',
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

        if options['migrate']:
            call_command('migrate', verbosity=options['verbosity'])
            call_command('createcachetable', verbosity=options['verbosity'])
