from d2qc.data.management.newline_command import NewlineCommand
from glodap.util.data_type_dict import DataTypeDict
from d2qc.data.models import DataTypeName, DataType

class Command(NewlineCommand):
    help = """
        Initalize data types and data type names in the database. This function
        uses the data type dictionary from the glodap library to initialize data
        types. If a data type or a data type name already exists, it is not
        changed.
    """
    def add_arguments(self, parser):
        parser.add_argument(
            '-u',
            '--update',
            action='store_true',
            help=(
                "Update existing data types. May roll back changes made "
                + "by other means in the database"
            ),
        )

    def handle(self, *args, **options):
        '''Insert data types'''
        data_types = DataTypeDict()
        reference_types = {}
        new_data_types = {}
        new_data_type_names = {}
        for key, data_type in data_types.items():
            if data_type.is_ref_type:
                if data_type.name in reference_types:
                    ref_type = reference_types[data_type.name]
                else:

                    ref_type, new = self._add_datatype(
                        name = data_type.name,
                        identifier = data_type.identifier,
                        update = options['update'],
                    )
                    if new:
                        new_data_types[ref_type.original_label] = ref_type
            elif data_type.parent_ref_type:
                if data_type.parent_ref_type.name in reference_types:
                    ref_type = reference_types[data_type.parent_ref_type.name]
                else:
                    ref_type, new = self._add_datatype(
                        name = data_type.parent_ref_type.name,
                        identifier = data_type.parent_ref_type.identifier,
                        update = options['update'],
                    )
                    if new:
                        new_data_types[ref_type.original_label] = ref_type
            else:
                # No reference type, skip this one
                continue
            reference_types[ref_type.original_label] = ref_type
            data_type_name, new = DataTypeName.objects.get_or_create(
                name = data_type.name,
            )
            if options['update'] and not new:
                if data_type_name.data_type_id != ref_type.id:
                    data_type_name.data_type_id = ref_type.id
                    data_type_name.save()
                    if options['verbosity'] > 0:
                        self.stdout.write(
                            f"Updated data type for {data_type_name}"
                        )
            if new:
                data_type_name.data_type_id = ref_type.id
                data_type_name.save()
                new_data_type_names[data_type_name.name] = data_type_name
        if options['verbosity'] > 0:
            if new_data_types or new_data_type_names:
                self.stdout.write(
                    "Data types initialized, the following was added"
                )
                if new_data_types:
                    self.stdout.write("Data Types:")
                    self.stdout.write(', '.join(map(str, new_data_types)))
                if new_data_type_names:
                    self.stdout.write("Data Type Names:")
                    self.stdout.write(', '.join(map(str, new_data_type_names)))
            else:
                self.stdout.write("""No new data types where added""")

    def _add_datatype(self, name, identifier, update):
        obj, new = DataType.objects.get_or_create(
            original_label = name,
        )
        if update and not new:
            if obj.identifier != identifier:
                obj.identifier = identifier
                obj.save()
                if options['verbosity'] > 0:
                    self.stdout.write(f"Updated identifier for {obj}")
        elif new:
            obj.identifier = identifier
            obj.save()

        return (obj, new)
