from django.conf import settings
from d2qc.data.management.newline_command import NewlineCommand
from d2qc.data.glodap.glodap import Glodap
from d2qc.data.models import DataFile
from django.core.management import call_command
from django.contrib.auth import login
from urllib.request import urlopen
import contextlib
import shutil
import os
import logging
import sys
import tempfile
import zipfile


class Command(NewlineCommand):
    help = """
        Import reference data from merged and adjusted glodap master file.
        See https://glodap.info for data files.
        Usage:
        manage.py import_refdata https://glodap.info/datafile.csv.zip \
            https://glodap.info/EXPOCODES.txt

        This will copy datafile.csv to the user data store, and import the data
        to the database, flagged as reference data. Data will be saved as user
        id 0, as you are not logged in as a user. You might need to clean out
        the database first.

        To clear reference data first, you can use:
        manage.py clear_refdata

        To start with a pristine database, you can use:

        manage.py clear_db -m
    """

    def add_arguments(self, parser):
        parser.add_argument(
            'data_filename',
            nargs='+',
            type=str,
            help='Reference input data file. Could be an url?',
        )
        parser.add_argument(
            'expocode_filename',
            nargs='+',
            type=str,
            help='Expocodes for data file',
        )

    def handle(self, *args, **options):
        '''Restore the database
        '''

        try:
            data_filename, data_basename = self.get_and_unpack(
                options['data_filename'][0]
            )

            final_path = DataFile.get_file_store_path(data_basename)
            final_dir = os.path.dirname(final_path)
            print(f"Move {data_filename} to {final_path}...")
            os.makedirs(final_dir, exist_ok=True)
            with contextlib.ExitStack() as stack:
                _from = stack.enter_context(open(data_filename))
                _to = stack.enter_context(open(final_path, 'w'))
                shutil.copyfileobj(_from, _to)
                os.remove(data_filename)
                data_filename = final_path

            expocode_filename, expocode_basename = self.get_and_unpack(
                options['expocode_filename'][0]
            )
            expocodes = None
            with open(expocode_filename) as f:
                expo = f.read().split()
                # print(expo)
                expocodes = dict(zip([int(f) for f in expo[0::2]], expo[1::2]))
                # print(expocodes)
            if expocodes:
                glodap = Glodap(data_filename, expocodes)
                glodap.fileImport()

        finally:
            os.remove(expocode_filename)

    def get_and_unpack(self, uri):
        fn, uri_extension = os.path.splitext(uri)
        uri_basename = os.path.basename(uri)
        if uri[0:4] == 'http': # is url
            print(f"Downloading {uri}...")
            fd, path = tempfile.mkstemp()
            with contextlib.ExitStack() as stack:
                _from = stack.enter_context(urlopen(uri))
                _to = stack.enter_context(open(path, 'wb'))
                shutil.copyfileobj(_from, _to)
            uri = path
        if uri_extension == '.zip':
            print(f"Extracting {uri}...")
            zip_file = zipfile.ZipFile(uri, 'r')
            fd, path = tempfile.mkstemp()
            with contextlib.ExitStack() as stack:
                _from = stack.enter_context(zip_file.open(zip_file.namelist()[0]))
                _to = stack.enter_context(open(path, 'wb'))
                shutil.copyfileobj(_from, _to)
                try:
                    os.remove(uri)
                except OSError as e:
                    pass
                uri = path
            uri_basename = uri_basename[:-4]
        return (uri, uri_basename)
