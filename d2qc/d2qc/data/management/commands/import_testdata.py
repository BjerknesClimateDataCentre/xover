# Import some test data to the database

from d2qc.data.management.newline_command import NewlineCommand
from d2qc.data.glodap.glodap import Glodap
import os


class Command(NewlineCommand):
    help = """
        Import some test-data into the database. Might be sufficient for
        testing user interface changes etc. For testing the actual crossover-
        functionality, use db_restore_from_prod instead.
    """
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
