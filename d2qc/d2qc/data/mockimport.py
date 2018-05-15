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



def importMockup():
    identifiers = [
        '06MT20091026',
        '45CE20110103',
        '58GS20090528',
    ]
    with open(settings.BASE_DIR + '/d2qc/data/refdata_cruises.json') as cruises:
        identifiers = json.load(cruises)

    for expocode in identifiers:
        importSingleMockup(expocode)


def importSingleMockup(expocode):
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
    str = ''
    for line in datastructure.readlines():
        str += line.decode('utf8')
    data = json.loads(str)
    data_set = d2qc.data.models.DataSet(
        expocode = data['info']['EXPOCODE'],
        is_reference = False)
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
        if (time[0:2] == '24'):
            time = '00' + time[2:4]
        unix_time_millis = datetime.datetime(
            int(date[0:4]),
            int(date[4:6]),
            int(date[6:8]),
            int(time[0:2]),
            int(time[2:4]),
        ).timestamp()
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
