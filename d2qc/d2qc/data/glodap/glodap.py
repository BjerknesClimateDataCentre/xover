from d2qc.data.models  import *
from glodap.util.data_type_dict import DataTypeDict
import datetime
import calendar
from django.contrib.gis.geos import Point
import os
# from d2qc.data.glodap.glodap import Glodap; Glodap().fileImport()

class Glodap:
    """
    Functionality to import glodap reference data
    """

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

    # These lines are possibly not trustworthy?
    # At least remove the h3 - data from these
    error_lines = {
        'h3':[
            # h3f - column has data values and not flags.
            19932,19934,19936,19938,19941,19942,19943,19944,19947,19948,19949,
            19950,19951,19957,19961,19965,19969,19972,19974,19977,19979,19981,
            19983,19990,19992,19995,19997,19998,20000,20003,20006,20007,20011,
            20012,20013,20014,20015,20016,20019,20022,20025,20030,20031,20032,
        ],
    }
    # The bad h3f - values:
    #       0.136,0.103,0.106,0.111,0.098,0.104,0.077,0.061,0.085,0.067,0.058,
    #       0.069,0.084,0.16 ,0.092,0.089,0.129,0.094,0.091,0.089,0.252,0.275,
    #       0.277,0.002,0.201,0.133,0.112,0.034,0.026,0.055,0.179,0.003,0.007,
    #       0.009,0.325,0.291,0.268,0.336,0.255,0.232,0.181,0.053,0.038,0.028,

    # Bad lines - 31 days in april: line 414278 to 414301. Switch these to next day

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
        'phts25p0': {
            'index': 48,
            'qcindex': 49,
            'qc2index': 52,
            'qcname': 'phts25p0f',
            'qc2name': 'phtsqc',
        },
        'phtsinsitutp': {
            'index': 50,
            'qcindex': 51,
            'qc2index': 52,
            'qcname': 'phtsinsitutpf',
            'qc2name': 'phtsqc',
        },
        'cfc11': {
            'index': 53,
            'qcindex': 55,
            'qc2index': 56,
            'qcname': 'cfc11f',
            'qc2name': 'cfc11qc',
        },
        'pcfc11': {
            'index': 54,
            'qcindex': None,
            'qc2index': None,
            'qcname': None,
            'qc2name': None,
        },
        'cfc12': {
            'index': 57,
            'qcindex': 59,
            'qc2index': 60,
            'qcname': 'cfc12f',
            'qc2name': 'cfc12qc',
        },
        'pcfc12': {
            'index': 58,
            'qcindex': None,
            'qc2index': None,
            'qcname': None,
            'qc2name': None,
        },
        'cfc113': {
            'index': 61,
            'qcindex': 63,
            'qc2index': 64,
            'qcname': 'cfc113f',
            'qc2name': 'cfc113qc',
        },
        'pcfc113': {
            'index': 62,
            'qcindex': None,
            'qc2index': None,
            'qcname': None,
            'qc2name': None,
        },
        'ccl4': {
            'index': 65,
            'qcindex': 67,
            'qc2index': 68,
            'qcname': 'ccl4f',
            'qc2name': 'ccl4qc',
        },
        'pccl4': {
            'index': 66,
            'qcindex': None,
            'qc2index': None,
            'qcname': None,
            'qc2name': None,
        },
        'sf6': {
            'index': 69,
            'qcindex': 71,
            'qc2index': None,
            'qcname': 'sf6f',
            'qc2name': None,
        },
        'psf6': {
            'index': 70,
            'qcindex': None,
            'qc2index': None,
            'qcname': None,
            'qc2name': None,
        },
        'c13': {
            'index': 72,
            'qcindex': 73,
            'qc2index': None,
            'qcname': 'c13f',
            'qc2name': None,
        },
        'c14': {
            'index': 74,
            'qcindex': 75,
            'qc2index': None,
            'qcname': 'c14f',
            'qc2name': None,
        },
        'c14err': {
            'index': 76,
            'qcindex': None,
            'qc2index': None,
            'qcname': None,
            'qc2name': None,
        },
        'h3': {
            'index': 77,
            'qcindex': 78, #0.136 line 9932 + 10000
            'qc2index': None,
            'qcname': 'h3f',
            'qc2name': None,
        },
        'h3err': {
            'index': 79,
            'qcindex': None,
            'qc2index': None,
            'qcname': None,
            'qc2name': None,
        },
        'he3': {
            'index': 80,
            'qcindex': 81,
            'qc2index': None,
            'qcname': 'he3f',
            'qc2name': None,
        },
        'he3err': {
            'index': 82,
            'qcindex': None,
            'qc2index': None,
            'qcname': None,
            'qc2name': None,
        },
        'he': {
            'index': 83,
            'qcindex': 84,
            'qc2index': None,
            'qcname': 'hef',
            'qc2name': None,
        },
        'heerr': {
            'index': 85,
            'qcindex': None,
            'qc2index': None,
            'qcname': None,
            'qc2name': None,
        },
        'neon': {
            'index': 86,
            'qcindex': 87,
            'qc2index': None,
            'qcname': 'neonf',
            'qc2name': None,
        },
        'neonerr': {
            'index': 88,
            'qcindex': None,
            'qc2index': None,
            'qcname': None,
            'qc2name': None,
        },
        'o18': {
            'index': 89,
            'qcindex': 90,
            'qc2index': None,
            'qcname': 'o18f',
            'qc2name': None,
        },
        'toc': {
            'index': 91,
            'qcindex': 92,
            'qc2index': None,
            'qcname': 'tocf',
            'qc2name': None,
        },
        'doc': {
            'index': 93,
            'qcindex': 94,
            'qc2index': None,
            'qcname': 'docf',
            'qc2name': None,
        },
        'don': {
            'index': 95,
            'qcindex': 96,
            'qc2index': None,
            'qcname': 'donf',
            'qc2name': None,
        },
        'tdn': {
            'index': 97,
            'qcindex': 98,
            'qc2index': None,
            'qcname': 'tdnf',
            'qc2name': None,
        },
        'chla': {
            'index': 99,
            'qcindex': 100,
            'qc2index': None,
            'qcname': 'chlaf',
            'qc2name': None,
        },
    }

    def fileImport(self, path = None, expocode_path = None, reference = True):
        if not path:
            # data/GLODAPv2 Merged Master File.csv
            path = os.path.join(
                    os.path.dirname(__file__),
                    'data/GLODAPv2_sorted.csv'
            )
        if not expocode_path:
            expocode_path = os.path.join(
                    os.path.dirname(__file__),
                    'data/EXPOCODES.txt'
            )
        line_no = 1
        # Make error_lines more useful as dicts
        for key in self.error_lines:
            self.error_lines[key] = dict(zip(
                    self.error_lines[key],
                    [True] * len(self.error_lines[key])
            ))

        try:
            filesize = os.path.getsize(path)
            progress = 0
            expo = open(expocode_path).read().split()
            expocodes = dict(zip(expo[0::2], expo[1::2]))

            with open(path) as infile:
                filename = os.path.basename(path)
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
                data_types = {}
                for var in vars:
                    type = DataType.objects.get_or_create(
                        identifier = DataTypeDict.getIdentFromVar(var),
                        original_label = var,
                    )
                    data_types[var] = type[0]

                current_station = Station
                current_cast = Cast
                current_data_set = DataSet
                current_depth = Depth
                platforms = {}
                for line in infile:
                    line_count += 1
                    all_new = False
                    progress += len(line.encode('utf-8'))
                    data = line.split(',')
                    try:
                        # DataSet
                        expocode = expocodes[data[idents['cruise']]]
                        if expocode != current_data_set.expocode:
                            data_set, created = DataSet.objects.get_or_create(
                                    expocode = expocode,
                                    is_reference = True,
                                    data_file = current_data_file
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
                            cast_no = int(data[idents['cast']])
                        if (
                                all_new
                                or cast_no != current_cast.cast
                        ):
                            current_cast = Cast(
                                    station = current_station,
                                    cast = cast_no
                            )
                            current_cast.save()
                            all_new = True

                        # Create date object from current line
                        try:
                            thetime = datetime.datetime(
                                    year=int(data[idents['year']]),
                                    month=int(data[idents['month']]),
                                    day=int(data[idents['day']]),
                                    hour=int(data[idents['hour']]),
                                    minute=int(data[idents['minute']]),
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
                                    int(data[idents['year']]),
                                    int(data[idents['month']])
                            )[1]
                            if int(data[idents['hour']]) > 23:
                                print(
                                        "Error hour {}, line {}" . format(
                                                data[idents['hour']],
                                                line_count
                                        )
                                )
                                thetime = datetime.datetime(
                                        year=int(data[idents['year']]),
                                        month=int(data[idents['month']]),
                                        day=int(data[idents['day']]),
                                        hour=int(data[idents['hour']]) - 24,
                                        minute=int(data[idents['minute']]),
                                        second=0,
                                        tzinfo=datetime.timezone.utc
                                )
                                thetime += datetime.timedelta(hours=24)
                            elif int(data[idents['day']]) > mon_days:
                                print(
                                        "Error day {}, line {}" . format(
                                                data[idents['day']],
                                                line_count
                                        )
                                )
                                thetime = datetime.datetime(
                                        year=int(data[idents['year']]),
                                        month=int(data[idents['month']]),
                                        day=int(data[idents['day']]) - mon_days,
                                        hour=int(data[idents['hour']]),
                                        minute=int(data[idents['minute']]),
                                        second=0,
                                        tzinfo=datetime.timezone.utc
                                )
                                thetime += datetime.timedelta(days=mon_days)
                            elif int(data[idents['minute']]) == 81:
                                # Random error, set minute to 0
                                print(
                                        "Error minute {}, line {}" . format(
                                                data[idents['minute']],
                                                line_count
                                        )
                                )
                                thetime = datetime.datetime(
                                        year=int(data[idents['year']]),
                                        month=int(data[idents['month']]),
                                        day=int(data[idents['day']]),
                                        hour=int(data[idents['hour']]),
                                        minute=0,
                                        second=0,
                                        tzinfo=datetime.timezone.utc
                                )
                            else:
                                print("UNHANDLED ERROR, line {}".format(
                                        line_count
                                ))



                        depth = float(data[idents['depth']])
                        bottle = int(data[idents['bottle']])

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

                            # Now insert the actual data
                            for key, var in self.glodap_vars.items():
                                if (
                                        key in self.error_lines
                                        and line_count in self.error_lines[key]
                                ):
                                    # some issue with this parameter
                                    print(
                                            'Skipping line ' + str(line_count)
                                            + ' for parameter ' + key
                                    )
                                    continue
                                value = float(data[var['index']])
                                qc_flag = None
                                if var['qcindex']:
                                    qc_flag = int(data[var['qcindex']])
                                qc2_flag = None
                                if var['qc2index']:
                                    qc2_flag = int(data[var['qc2index']])
                                model_value = DataValue(
                                        depth = current_depth,
                                        value = value,
                                        qc_flag = qc_flag,
                                        qc2_flag = qc2_flag,
                                        data_type = data_types[key]
                                )
                                current_value = model_value
                                model_value.save()
                    except Exception as e:
                        print(e)
                        print(line)
#                        print('Timestamp error: ' + str(current_data_set.expocode) + ' - line: ' + str(line_count))
                        all_new = False
                        return
                        continue

                    # Progress
                    if line_count % 10000 == 0:
                        print("Processed {}% of file {}".format(
                                str(int(progress / filesize * 100)),
                                filename
                        ))
                    all_new = False

                print("Processed {}% of file {}".format(
                        str(int(progress / filesize * 100)),
                        filename
                ))

        except FileNotFoundError:
            print("Some error")

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
