from django.core.management import call_command
from d2qc.data.management.newline_command import NewlineCommand
from django.core.cache import cache
from d2qc.data.glodap.glodap import Glodap;
from django.conf import settings
import os



class Command(NewlineCommand):
    help = """Clear cache for the application"""
    def handle(self, *args, **options):
        db_name = settings.DATABASES['default']['NAME']
        user = settings.DATABASES['default']['USER']
        initdb_path = settings.INITDB_PATH
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

        # Migrate to current schema
        call_command('migrate')

        Glodap().fileImport()
