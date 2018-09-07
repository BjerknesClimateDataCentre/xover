############################################
#
# Simple import script. Run like this:
# cd project-folder
# Activate python environment
# cd d2qc
# python manage.py shell
# import d2qc.data.mockimport; d2qc.data.mockimport.importMockup()
#
############################################

import d2qc.data.models
from d2qc.data.data_type_dict import DataTypeDict
import datetime
import urllib.request
import json
from django.conf import settings



def importMockup(reference = False):
    identifiers = [
        '06MT20091026',
        '45CE20110103',
        '58GS20090528',
    ]
    if reference:
        with open(settings.BASE_DIR + '/d2qc/data/refdata_cruises.json') as cruises:
            identifiers = json.load(cruises)

    for expocode in identifiers:
        importSingleMockup(expocode)


def importSingleMockup(expocode, reference = False):
    ignore = {
        'EXPOCODE': 1,
        'SECT_ID': 1,
        'DATE': 1,
        'TIME': 1,
        'LATITUDE': 1,
        'LONGITUDE': 1,
        'DEPTH': 1,
    }
    datastructure = urllib.request.urlopen('http://127.0.0.1:8000/mockup/?ident=' + expocode)
    tmpstr = ''
    for line in datastructure.readlines():
        tmpstr += line.decode('utf8')
    data = json.loads(tmpstr)
    data_set = d2qc.data.models.DataSet(
        expocode = data['info']['EXPOCODE'],
        is_reference = reference)
    data_set.save()

    # First get Data Types
    data_types = {}
    for param in data['data']:
        data_unit = None
        if data['data'][param]['unit']:
            data_unit =  d2qc.data.models.DataUnit.objects.get_or_create(
                identifier = DataTypeDict.getIdentFromVar(data['data'][param]['unit']),
                original_label = data['data'][param]['unit'],
            )
            data_unit = data_unit[0]

        data_type = d2qc.data.models.DataType.objects.get_or_create(
            identifier = DataTypeDict.getIdentFromVar(param),
            original_label = param,
            data_unit = data_unit,
        )
        data_types[param] = data_type[0]

    count = 0
    for date in data['data']['DATE']['values']:
        time = data['data']['TIME']['values'][count]
        # Oops: Line 1683 in 316N20050821.exc.csv has time = 2400
        # Date errors in file 318M19940327: 31 days in april.
        # (Lines 3435,3436,3437,3438,3439,3440,3441,3442,3443,3444,3445,3446,
        # 3447,3448,3449,3450,3451,3452,3453,3454,3455,3456,3457,3458)
        # Date errors in 318M20091121, lines 1424,1543,2779,5360
        # Date errors in 320620000000, lines 18134,18472,18804,18134,18472,
        # 18804,18134,18472,18804,18134,18472,18804,18134,18472,18804,18134,
        # 18472,18804,18134,18472,18804,18134,18472,18804,18134,18472,18804
        # Date errors in 33RR20080204, lines 561,660
        # Date errors in 33RR20090320, lines 265,607,1293,1780,1957,2105,3667,
        # 6240
        # Date errors in 64PE20050907, lines 591,592,593,594,595,596,597,598,
        # 599,600,601,602,603,604,605,606,607,608
        # Date errors in 74DI20041103, lines 830,831,832,833,834,835,836,837,
        # 838,839,840,841,842,843,844,845,846,847,848,849,850,851,852,853
        # Date errors in IcelandSea, lines 885,886,887,888,889,890,891,892,893,
        # 894,895,896,897,898,899,900,901,902,903,904,905,906


        try:
            unix_time_millis = datetime.datetime(
                int(date[0:4]),
                int(date[4:6]),
                int(date[6:8]),
                int(time[0:2]),
                int(time[2:4]),
            ).timestamp() * 1000 # multiply to get milliseconds
        except:
            print('Timestamp error: ' + expocode + ' - line: ' + str(count))
            count += 1
            continue
        latitude = data['data']['LATITUDE']['values'][count]
        longitude = data['data']['LONGITUDE']['values'][count]
        depth = data['data']['DEPTH']['values'][count]
        station_number = None
        if data['data'].get('STNNBR'):
            station_number = data['data']['STNNBR']['values'][count]
        data_point = d2qc.data.models.DataPoint(
            data_set = data_set,
            latitude = latitude,
            longitude = longitude,
            depth = depth,
            station_number = station_number,
            unix_time_millis = unix_time_millis
        )
        data_point.save()
        for param in data['data']:
            data_type = data_types[param]
            if ignore.get(param, 0) == 0:
                value = data['data'][param]['values'][count]
                d2qc.data.models.DataValue(
                    data_point = data_point,
                    data_type = data_type,
                    value = value
                ).save()
        count += 1
