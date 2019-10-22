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
        Import reference data from merged and adjusted glodap master file,
        see https://glodap.info
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

        data_filename = options['data_filename'][0]
        fn, data_file_extension = os.path.splitext(data_filename)
        expocode_filename = options['expocode_filename'][0]
        data_basename = os.path.basename(data_filename)
        tmpfiles = []
        try:
            if data_filename[0:4] == 'http': # is url
                print(f"Downloading {data_filename}...")
                fd, path = tempfile.mkstemp()
                tmpfiles.append(path)
                with contextlib.ExitStack() as stack:
                    _from = stack.enter_context(urlopen(data_filename))
                    _to = stack.enter_context(open(path, 'wb'))
                    shutil.copyfileobj(_from, _to)
                data_filename = path
            if data_file_extension == '.zip':
                print(f"Extracting {data_filename}...")
                zip_file = zipfile.ZipFile(data_filename, 'r')
                fd, path = tempfile.mkstemp()
                tmpfiles.append(path)
                with contextlib.ExitStack() as stack:
                    _from = stack.enter_context(zip_file.open(zip_file.namelist()[0]))
                    _to = stack.enter_context(open(path, 'wb'))
                    shutil.copyfileobj(_from, _to)
                    data_filename = path
                data_basename = data_basename[:-4]

            final_path = DataFile.get_file_store_path(data_basename)
            final_dir = os.path.dirname(final_path)
            print(f"Move {data_filename} to {final_path}...")
            os.makedirs(final_dir, exist_ok=True)
            with contextlib.ExitStack() as stack:
                _from = stack.enter_context(open(data_filename))
                _to = stack.enter_context(open(final_path, 'w'))
                shutil.copyfileobj(_from, _to)
                data_filename = final_path
            print("In the end: " + data_filename)
        finally:
            for f in tmpfiles:
                os.remove(f)
