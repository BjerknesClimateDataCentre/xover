from d2qc.data.management.newline_command import NewlineCommand
import d2qc.data.models as models

class Command(NewlineCommand):
    help = """
        This command is mainly used internally to import files in the
        background.
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
            seconds = (
                    data_file.import_finnished - data_file.import_started
            ).total_seconds()
            self.stdout.write(self.style.SUCCESS(
                    "Import finnished in {} seconds".format(int(seconds))
            ))
            if data_file.import_errors:
                self.stdout.write(self.style.NOTICE(
                        "INFO: {}".format(data_file.import_errors)
                ))
