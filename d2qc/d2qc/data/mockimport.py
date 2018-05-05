import d2qc.data.models
import datetime
import urllib.request
import json

def importMockup():
    identifiers = {
        '06MT20091026',
        '45CE20110103',
        '58GS20090528',
    }

    ignore = {
        'EXPOCODE': 1,
        'SECT_ID': 1,
        'DATE': 1,
        'TIME': 1,
        'LATITUDE': 1,
        'LONGITUDE': 1,
        'DEPTH': 1,
    }


    for ident in identifiers:
        datastructure = urllib.request.urlopen('http://127.0.0.1:8000/mockup/?ident=' + ident)
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
            data_type = d2qc.data.models.DataType.objects.get_or_create(
                    name = param,
                    unit = data['data'][param]['unit']
            )
            data_type = data_type[0]
            #dir(data_type)
            data_type.save()
            data_types[param] = data_type

        count = 0
        for date in data['data']['DATE']['values']:
            time = data['data']['TIME']['values'][count]
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
