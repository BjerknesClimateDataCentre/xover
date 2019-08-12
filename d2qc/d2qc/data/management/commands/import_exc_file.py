from django.core.management.base import BaseCommand
import d2qc.data.models as models

class Command(BaseCommand):
    """
    This command is mainly used internally to import files in the background.
    """
    def add_arguments(self, parser):
        parser.add_argument(
            'data_file_id',
            nargs='+',
            type=int,
            help='Import this data file',
        )

    def handle(self, *args, **options):
        pk = options['data_file_id'][0]
        data_file = models.DataFile.objects.get(pk=pk)
        data_file.import_data()
        if options['verbosity'] > 0:
            self.stdout.write(self.style.SUCCESS("Import finnished"))
