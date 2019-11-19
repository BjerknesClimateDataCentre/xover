from d2qc.data.management.newline_command import NewlineCommand
import d2qc.data.models as models
from django.contrib.auth.models import User



class Command(NewlineCommand):
    help = """
        This command is used to normalize the reference data in the database.
        The function loops over the reference data sets, and normalizes the
        alkalinity and co2 data against salinity. Data sets / parameters that
        are already normalized are excluded.

        This functions generally takes a few minutes to run.
    """

    def handle(self, *args, **options):

        user = User(profile=models.Profile())
        for data_set in models.DataSet.objects.filter(is_reference=True):
            data_type_names = data_set.getNormalizableParameters(user.profile)
            for data_type_name in data_type_names:
                try:
                    data_set.normalize_data(
                        data_type_name.id,
                        user
                    )
                except Exception as e:
                    self.stderr.write(f"{e}")


            if options['verbosity']>1:
                self.stdout.write(f"Normalized data set {data_set}")



