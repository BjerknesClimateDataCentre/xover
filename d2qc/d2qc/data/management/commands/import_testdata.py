# Import some test data to the database

from django.core.management.base import BaseCommand
from d2qc.data.glodap.glodap import Glodap
import os


class Command(BaseCommand):

    def handle(self, *args, **options):
        testdata = os.path.join(
            os.path.dirname(__file__),
            'data/GLODAPv2_first_5_datasets.csv'
        )
        expocodes = os.path.join(
            os.path.dirname(testdata),
            'EXPOCODES.txt'
        )
        print(testdata)
        Glodap().fileImport(testdata, expocodes)
