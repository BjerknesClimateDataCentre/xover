from d2qc.data.models  import *
from glodap.util.data_type_dict import DataTypeDict
import datetime
import calendar
from django.contrib.gis.geos import Point
import os
import gsw
from django.contrib.auth import authenticate, login

class Glodap:
    """
    Functionality to import glodap reference data
    """
    data_file_path = None
    expocodes = None

    glodap_identificators = {
        'cruise': 0,
        'station': 1,
        'cast': 2,
        'year': 3,
        'month': 4,
        'day': 5,
        'hour': 6,
        'minute': 7,
        'latitude': 8,
        'longitude': 9,
        'bottomdepth': 10,
        'bottle': 12,
        'depth': 14,
    }

    glodap_vars = {
        'pressure': {
            'index': 13,
            'qcindex': None,
            'qc2index': None,
            'qcname': None,
            'qc2name': None,
        },
        'temperature': {
            'index': 15,
            'qcindex': None,
            'qc2index': None,
            'qcname': None,
            'qc2name': None,
        },
        'theta': {
            'index': 16,
            'qcindex': None,
            'qc2index': None,
            'qcname': None,
            'qc2name': None,
        },
        'salinity': {
            'index': 17,
            'qcindex': 18,
            'qc2index': 19,
            'qcname': 'salinityf',
            'qc2name': 'salinityqc',
        },
        'sigma0': {
            'index': 20,
            'qcindex': None,
            'qc2index': None,
            'qcname': None,
            'qc2name': None,
        },
        'sigma1': {
            'index': 21,
            'qcindex': None,
            'qc2index': None,
            'qcname': None,
            'qc2name': None,
        },
        'sigma2': {
            'index': 22,
            'qcindex': None,
            'qc2index': None,
            'qcname': None,
            'qc2name': None,
        },
        'sigma3': {
            'index': 23,
            'qcindex': None,
            'qc2index': None,
            'qcname': None,
            'qc2name': None,
        },
        'sigma4': {
            'index': 24,
            'qcindex': None,
            'qc2index': None,
            'qcname': None,
            'qc2name': None,
        },
        'gamma': {
            'index': 25,
            'qcindex': None,
            'qc2index': None,
            'qcname': None,
            'qc2name': None,
        },
        'oxygen': {
            'index': 26,
            'qcindex': 27,
            'qc2index': 28,
            'qcname': 'oxygenf',
            'qc2name': 'oxygenqc',
        },
        'aou': {
            'index': 29,
            'qcindex': 30,
            'qc2index': None,
            'qcname': 'aouf',
            'qc2name': None,
        },
        'nitrate': {
            'index': 31,
            'qcindex': 32,
            'qc2index': 33,
            'qcname': 'nitratef',
            'qc2name': 'nitrateqc',
        },
        'nitrite': {
            'index': 34,
            'qcindex': 35,
            'qc2index': None,
            'qcname': 'nitritef',
            'qc2name': 'nitriteqc',
        },
        'silicate': {
            'index': 36,
            'qcindex': 37,
            'qc2index': 38,
            'qcname': 'silicatef',
            'qc2name': 'silicateqc',
        },
        'phosphate': {
            'index': 39,
            'qcindex': 40,
            'qc2index': 41,
            'qcname': 'phosphatef',
            'qc2name': 'phosphateqc',
        },
        'tco2': {
            'index': 42,
            'qcindex': 43,
            'qc2index': 44,
            'qcname': 'tco2f',
            'qc2name': 'tco2qc',
        },
        'talk': {
            'index': 45,
            'qcindex': 46,
            'qc2index': 47,
            'qcname': 'talkf',
            'qc2name': 'talkqc',
        },
        'fco2': {
            'index': 48,
            'qcindex': 49,
            'qc2index': 50,
            'qcname': 'fco2f',
            'qc2name': 'fco2temp',
        },
        'phts25p0': {
            'index': 51,
            'qcindex': 52,
            'qc2index': 55,
            'qcname': 'phts25p0f',
            'qc2name': 'phtsqc',
        },
        'phtsinsitutp': {
            'index': 53,
            'qcindex': 54,
            'qc2index': 55,
            'qcname': 'phtsinsitutpf',
            'qc2name': 'phtsqc',
        },
        'cfc11': {
            'index': 56,
            'qcindex': 58,
            'qc2index': 59,
            'qcname': 'cfc11f',
            'qc2name': 'cfc11qc',
        },
        'pcfc11': {
            'index': 57,
            'qcindex': None,
            'qc2index': None,
            'qcname': None,
            'qc2name': None,
        },
        'cfc12': {
            'index': 60,
            'qcindex': 62,
            'qc2index': 63,
            'qcname': 'cfc12f',
            'qc2name': 'cfc12qc',
        },
        'pcfc12': {
            'index': 61,
            'qcindex': None,
            'qc2index': None,
            'qcname': None,
            'qc2name': None,
        },
        'cfc113': {
            'index': 64,
            'qcindex': 66,
            'qc2index': 67,
            'qcname': 'cfc113f',
            'qc2name': 'cfc113qc',
        },
        'pcfc113': {
            'index': 65,
            'qcindex': None,
            'qc2index': None,
            'qcname': None,
            'qc2name': None,
        },
        'ccl4': {
            'index': 68,
            'qcindex': 70,
            'qc2index': 71,
            'qcname': 'ccl4f',
            'qc2name': 'ccl4qc',
        },
        'pccl4': {
            'index': 69,
            'qcindex': None,
            'qc2index': None,
            'qcname': None,
            'qc2name': None,
        },
        'sf6': {
            'index': 72,
            'qcindex': 74,
            'qc2index': None,
            'qcname': 'sf6f',
            'qc2name': None,
        },
        'psf6': {
            'index': 73,
            'qcindex': None,
            'qc2index': None,
            'qcname': None,
            'qc2name': None,
        },
        'c13': {
            'index': 75,
            'qcindex': 76,
            'qc2index': 77,
            'qcname': 'c13f',
            'qc2name': 'c13qc',
        },
        'c14': {
            'index': 78,
            'qcindex': 79,
            'qc2index': None,
            'qcname': 'c14f',
            'qc2name': None,
        },
        'c14err': {
            'index': 80,
            'qcindex': None,
            'qc2index': None,
            'qcname': None,
            'qc2name': None,
        },
        'h3': {
            'index': 81,
            'qcindex': 82, #0.136 line 9932 + 10000
            'qc2index': None,
            'qcname': 'h3f',
            'qc2name': None,
        },
        'h3err': {
            'index': 83,
            'qcindex': None,
            'qc2index': None,
            'qcname': None,
            'qc2name': None,
        },
        'he3': {
            'index': 84,
            'qcindex': 85,
            'qc2index': None,
            'qcname': 'he3f',
            'qc2name': None,
        },
        'he3err': {
            'index': 86,
            'qcindex': None,
            'qc2index': None,
            'qcname': None,
            'qc2name': None,
        },
        'he': {
            'index': 87,
            'qcindex': 88,
            'qc2index': None,
            'qcname': 'hef',
            'qc2name': None,
        },
        'heerr': {
            'index': 89,
            'qcindex': None,
            'qc2index': None,
            'qcname': None,
            'qc2name': None,
        },
        'neon': {
            'index': 90,
            'qcindex': 91,
            'qc2index': None,
            'qcname': 'neonf',
            'qc2name': None,
        },
        'neonerr': {
            'index': 92,
            'qcindex': None,
            'qc2index': None,
            'qcname': None,
            'qc2name': None,
        },
        'o18': {
            'index': 93,
            'qcindex': 94,
            'qc2index': None,
            'qcname': 'o18f',
            'qc2name': None,
        },
        'toc': {
            'index': 95,
            'qcindex': 96,
            'qc2index': None,
            'qcname': 'tocf',
            'qc2name': None,
        },
        'doc': {
            'index': 97,
            'qcindex': 98,
            'qc2index': None,
            'qcname': 'docf',
            'qc2name': None,
        },
        'don': {
            'index': 99,
            'qcindex': 100,
            'qc2index': None,
            'qcname': 'donf',
            'qc2name': None,
        },
        'tdn': {
            'index': 101,
            'qcindex': 102,
            'qc2index': None,
            'qcname': 'tdnf',
            'qc2name': None,
        },
        'chla': {
            'index': 103,
            'qcindex': 104,
            'qc2index': None,
            'qcname': 'chlaf',
            'qc2name': None,
        },
    }

    def __init__(self, data_file_path, expocodes):
        """
        Initalize the Glodap object with a path to the file with glodap data
        (can be an url) and a dict containing {int: 'expocode', ...}
        The data file only contains an integer cruise number, so this needs to
        match the int in the expocode dict to obtain the expocodes.
        Files can be downloaded from https://www.glodap.info

        data_file_path  Url or file path to a (possibly zipped) glodap
                        dataset file
        expocodes       dict with format {int:expocode ...} like
                        {1:'06AQ19840719', 2:'06AQ19860627',...}
        """
        self.data_file_path = data_file_path
        self.expocodes = expocodes

    def fileImport(self, reference = True):
        """
        Import Glodap reference file to the database. This will take time ...

        reference       If set to True, data-sets are stored with the
                        is_reference - flag set to true.
        """
        line_no = 1
        errors = []
        start = datetime.datetime.now()

        try:
            filesize = os.path.getsize(self.data_file_path)
            progress = 0

            with open(self.data_file_path) as infile:
                filename = os.path.basename(self.data_file_path)
                if DataFile.objects.filter(filepath=filename).exists():
                    print('File already exists')
                    return
                else:
                    print('Import file ' + filename)

                name = os.path.splitext(filename)[0]


                # Read the file header line
                headers = infile.readline()
                line_count = 1 # actual line handled in the file.

                progress += len(headers.encode('utf-8'))

                # Check that file layout is OK
                if not self.glodapFileLayoutIsOK(headers):
                    return

                current_data_file, created = DataFile.objects.get_or_create(
                                filepath = filename,
                                name = name,
                                headers = headers
                        )

                # Import data types
                vars = self.glodap_vars
                idents = self.glodap_identificators
                data_type_names = {}
                data_type_dict = DataTypeDict()
                for var in vars:
                    data_type, created = DataType.objects.get_or_create(
                        identifier = data_type_dict.getIdentifier(var),
                        original_label = var,
                    )
                    data_type_name = DataTypeName.objects.get_or_create(
                        name = var,
                        data_type = data_type
                    )
                    data_type_names[var] = data_type_name[0]

                temp_aut = DataTypeName.objects.filter(name="temperature").first()
                salin_aut = DataTypeName.objects.filter(name="salinity").first()
                press_aut = DataTypeName.objects.filter(name="pressure").first()

                current_station = Station()
                current_cast = Cast()
                current_data_set = DataSet()
                current_depth = Depth()
                platforms = {}
                value_list = []
                for line in infile:
                    line_count += 1
                    all_new = False
                    progress += len(line.encode('utf-8'))
                    data = line.split(',')
                    try:
                        # DataSet
                        expocode = self.expocodes[int(float(data[idents['cruise']]))]
                        if expocode != current_data_set.expocode:
                            data_set, created = DataSet.objects.get_or_create(
                                    expocode = expocode,
                                    is_reference = True,
                                    data_file = current_data_file,
                                    temp_aut = temp_aut,
                                    salin_aut = salin_aut,
                                    press_aut = press_aut,
                            )
                            current_data_set = data_set
                            all_new = True

                        station_number = -1
                        if data[idents['station']]:
                            station_number = int(float(data[idents['station']]))

                        # Station
                        if (
                                all_new
                                or station_number != current_station.station_number
                        ):
                            latitude = float(data[idents['latitude']])
                            longitude = float(data[idents['longitude']])

                            current_station = Station(
                                    data_set = current_data_set,
                                    position = Point(longitude, latitude),
                                    station_number = station_number,
                            )
                            current_station.save()
                            all_new = True

                        # Cast
                        cast_no = -1
                        if data[idents['cast']]:
                            cast_no = int(float(data[idents['cast']]))
                        if (
                                all_new
                                or cast_no != current_cast.cast
                        ):
                            current_cast = Cast(
                                    station = current_station,
                                    cast = int(float(cast_no))
                            )
                            current_cast.save()
                            all_new = True

                        # Create date object from current line
                        try:
                            thetime = datetime.datetime(
                                    year=int(float(data[idents['year']])),
                                    month=int(float(data[idents['month']])),
                                    day=int(float(data[idents['day']])),
                                    hour=int(float(data[idents['hour']])),
                                    minute=int(float(data[idents['minute']])),
                                    second=0,
                                    tzinfo=datetime.timezone.utc
                            )
                        except ValueError as e:
                            print(str(line_count), end='|', flush=True)
                            print(e)
                            # If hour is 24 or more, we subtract 24, and add 24
                            # hours afterwards to the created date object
                            # Similarly, if day is more than number of days for
                            # a given month, we subtract the number of days in
                            # the month, and add the same value to the date
                            # object.
                            mon_days = calendar.monthrange(
                                    int(float(data[idents['year']])),
                                    int(float(data[idents['month']])),
                            )[1]
                            if int(float(data[idents['hour']])) > 23:
                                print(
                                        "Error hour {}, line {}" . format(
                                                data[idents['hour']],
                                                line_count
                                        )
                                )
                                thetime = datetime.datetime(
                                        year=int(float(data[idents['year']])),
                                        month=int(float(data[idents['month']])),
                                        day=int(float(data[idents['day']])),
                                        hour=int(float(data[idents['hour']])) - 24,
                                        minute=int(float(data[idents['minute']])),
                                        second=0,
                                        tzinfo=datetime.timezone.utc
                                )
                                thetime += datetime.timedelta(hours=24)
                            elif int(float(data[idents['day']])) > mon_days:
                                print(
                                        "Error day {}, line {}" . format(
                                                data[idents['day']],
                                                line_count
                                        )
                                )
                                thetime = datetime.datetime(
                                        year=int(float(data[idents['year']])),
                                        month=int(float(data[idents['month']])),
                                        day=int(float(data[idents['day']])) - mon_days,
                                        hour=int(float(data[idents['hour']])),
                                        minute=int(float(data[idents['minute']])),
                                        second=0,
                                        tzinfo=datetime.timezone.utc
                                )
                                thetime += datetime.timedelta(days=mon_days)
                            elif int(float(data[idents['minute']])) == 81:
                                # Random error, set minute to 0
                                print(
                                        "Error minute {}, line {}" . format(
                                                data[idents['minute']],
                                                line_count
                                        )
                                )
                                thetime = datetime.datetime(
                                        year=int(float(data[idents['year']])),
                                        month=int(float(data[idents['month']])),
                                        day=int(float(data[idents['day']])),
                                        hour=int(float(data[idents['hour']])),
                                        minute=0,
                                        second=0,
                                        tzinfo=datetime.timezone.utc
                                )
                            else:
                                print("UNHANDLED ERROR, line {}".format(
                                        line_count
                                ))



                        depth = float(data[idents['depth']])
                        bottle = int(float(data[idents['bottle']]))

                        # Depth
                        if (
                                all_new
                                or depth != current_depth.depth
                                or bottle != current_depth.bottle
                                or thetime != current_depth.date_and_time
                        ):
                            model_depth = Depth(
                                    cast = current_cast,
                                    depth = depth,
                                    bottle = bottle,
                                    date_and_time = thetime,
                            )
                            current_depth = model_depth
                            model_depth.save()
                            all_new = True

                            temp_val = salin_val = press_val = None
                            # Now insert the actual data
                            append_to_list = []
                            for key, var in self.glodap_vars.items():
                                value = float(data[var['index']])
                                qc_flag = None
                                if var['qcindex']:
                                    qc_flag = int(float(data[var['qcindex']]))
                                qc2_flag = None
                                if var['qc2index']:
                                    qc2_flag = int(float(data[var['qc2index']]))
                                model_value = DataValue(
                                        depth = current_depth,
                                        value = value,
                                        qc_flag = qc_flag,
                                        qc2_flag = qc2_flag,
                                        data_type_name = data_type_names[key]
                                )
                                current_value = model_value
                                append_to_list.append(model_value)
                                # collect temp, press, salin values
                                # value = -999 or similar means missing value
                                value = value if value > -8 else None
                                if key == temp_aut.name:
                                    temp_val = value
                                if key == salin_aut.name:
                                    salin_val = value
                                if key == press_aut.name:
                                    press_val = value

                            # If all are set, we can calculate sigma4
                            if not None in [temp_val, salin_val, press_val]:
                                try:
                                    sigma4 = gsw.density.sigma4(
                                        gsw.conversions.SA_from_SP(
                                            salin_val,
                                            press_val,
                                            longitude,
                                            latitude,
                                        ),
                                        temp_val,
                                    )
                                    current_depth.sigma4 = sigma4
                                    current_depth.save()
                                    value_list += append_to_list

                                except Exception as e:
                                    pass
                    except Exception as e:
                        error = e
                        print(f"Line no {line_count}: {error}")
                        errors += [f"Line no {line_count}: {error}"]

                        all_new = False
                        if value_list:
                            DataValue.objects.bulk_create(value_list)
                            value_list = []
                        continue

                    # Insert the values in bulk
                    if line_count % 300 == 0 and value_list:
                        print('.', end='', flush=True)
                        DataValue.objects.bulk_create(value_list)
                        value_list = []

                    # Progress
                    if line_count % 10000 == 0:
                        print("Processed {}% of file {}".format(
                                str(int(progress / filesize * 100)),
                                filename
                        ))
                    all_new = False

                if value_list:
                    DataValue.objects.bulk_create(value_list)
                    value_list = []

                print("Processed {}% of file {}".format(
                        str(int(progress / filesize * 100)),
                        filename
                ))

        except FileNotFoundError:
            print("File not found")
        print('\n'.join(errors))

        end = datetime.datetime.now()
        print(f"Time elapsed: {end-start}")


    def glodapFileLayoutIsOK(self, headers):

        vars = self.glodap_vars
        file_vars = headers.split(',')
        ok = True
        for key in vars:
            if file_vars[vars[key]['index']].strip() != key:
                print("Wrong file layout for variable " + key)
                ok = False
            if (vars[key]['qcindex'] and
                    file_vars[vars[key]['qcindex']].strip() != vars[key]['qcname']):
                print("Wrong file layout for variable " + vars[key]['qcname'])
                ok = False
            if (vars[key]['qc2index'] and
                    file_vars[vars[key]['qc2index']].strip() != vars[key]['qc2name']):
                print("Wrong file layout for variable " + vars[key]['qc2name'])
                ok = False
        idents = self.glodap_identificators
        for key in idents:
            if file_vars[idents[key]].strip() != key:
                print("Wrong file layout for identificator " + key)
                ok = False
        return ok
