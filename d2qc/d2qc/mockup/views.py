from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotFound
import os.path
import csv
import collections
from django.http import JsonResponse

def index(request):
    data_folder = os.path.dirname(os.path.abspath(__file__)) + '/data'
    data_ident = request.GET.get('ident','')
    data_file = "%s/%s/%s.exc.csv" % (data_folder, data_ident, data_ident)
    retval = ''
    response =  HttpResponse()
    if os.path.isfile(data_file):
        enc='iso-8859-1'
        with open(data_file, 'r', newline='', encoding=enc) as file:
            headers = []
            headers.append(file.readline().strip())
            pos = file.tell()
            line = file.readline()
            while line[0] == '#':
                headers.append(line.strip())
                pos = file.tell()
                line = file.readline()
            file.seek(pos)
            datareader = csv.reader(file, delimiter=',', quotechar='|')
            counter = 0
            data = collections.OrderedDict()
            for row in datareader:
                if len(row) == 0:
                    counter += 1
                    continue;
                elif counter == 0:
                    # Create column headers
                    for name in row:
                        name = name.strip()
                        data[name] = {'values':[], 'unit': ''}
                elif counter == 1:
                    i = 0
                    # Append units to columns if exist
                    for name in data:
                        unit = row[i].strip()
                        if unit:
                            data[name]['unit'] = unit
                        i += 1
                elif row[0].strip() == 'END_DATA':
                    break
                else:
                    # Add data to each column
                    i = 0
                    for name in data:
                        data[name]['values'].append(row[i].strip())
                        i += 1
                counter += 1
            info = {
                'COUNT': counter,
                'EXPOCODE': data_ident,
                'FILENAME': data_file,
            }
            data = {'headers': headers, 'data': data, 'info': info}
            response = JsonResponse(data)
    else:
        response = HttpResponseNotFound()

    return response
