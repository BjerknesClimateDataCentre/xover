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
                    ref_type, created = DataType.objects.get_or_create(
                        identifier = data_type.identifier,
                        original_label = data_type.name,
                    )
                    if created:
                        new_data_types[ref_type.original_label] = ref_type
            elif data_type.parent_ref_type:
                if data_type.parent_ref_type.name in reference_types:
                    ref_type = reference_types[data_type.parent_ref_type.name]
                else:
                    ref_type, created = DataType.objects.get_or_create(
                        identifier = data_type.parent_ref_type.identifier,
                        original_label = data_type.parent_ref_type.name,
                    )
                    if created:
                        new_data_types[ref_type.original_label] = ref_type
            else:
                # No reference type, skip this one
                continue
            reference_types[ref_type.original_label] = ref_type
            data_type_name, created = DataTypeName.objects.get_or_create(
                name = data_type.name,
                data_type = ref_type,
            )
            if created:
                new_data_type_names[data_type_name.name] = data_type_name
        if options['verbosity'] > 0:
            print("""Data types initialized. """, end='')
            if new_data_types or new_data_type_names:
                print("""The following was added""")
                if new_data_types:
                    print("Data Types:")
                    print(', '.join(map(str, new_data_types)))
                if new_data_type_names:
                    print("Data Type Names:")
                    print(', '.join(map(str, new_data_type_names)))
            print("")
