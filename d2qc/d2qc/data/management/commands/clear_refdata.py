from d2qc.data.management.newline_command import NewlineCommand
from d2qc.data import models
from random import SystemRandom

class Command(NewlineCommand):
    help = """
        Delete all datasets marked as is_reference, including all related data.
        This funtion takes some minutes to run, could be optimized if neccessary
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '-f',
            '--force',
            action='store_true',
            help='No prompt weather you really want to do this',
        )

    def handle(self, *args, **options):
        clear_it = options['force']
        if not clear_it:
            _input = input('Really clear all reference data (yes/No):')
            if _input == 'yes':
                clear_it = True

        if clear_it:
            count = models.DataSet.objects.filter(is_reference=True).count()
            row = 0
            used = -1
            for dataset in models.DataSet.objects.filter(is_reference=True):
                percent = round(row/count*100)
                if options['verbosity'] > 0:
                    if percent % 10 == 0 and used != percent:
                        print(f"\nDeleted {percent}% ")
                        used = percent
                    print('.', end='', flush=True)
                row += 1
                dataset.delete()
            if options['verbosity'] > 0:
                print("\nReference data deleted")

        elif options['verbosity'] > 0:
            pulp_fiction = [
                "You read the Bible, Brett?",
                """They call it "Royale with cheese" """,
                "Zed's dead, baby. Zed's dead.",
                "Would you give a guy a foot massage?",
            ]
            print(SystemRandom().choice(pulp_fiction))
            print("No data was deleted")
