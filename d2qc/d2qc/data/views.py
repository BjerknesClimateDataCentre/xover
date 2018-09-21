import d2qc.data as data
import os.path
import os
from django.http import HttpResponse
from django.db.models import Max, Min, Count, Q
from django.template import loader
from d2qc.data.models import DataSet, DataPoint, DataType, DataValue, DataUnit
from rest_framework import viewsets
from d2qc.data.serializers import *
from rest_framework.decorators import api_view
from rest_framework.response import Response
from d2qc.data.sql import *
from lib.d2qc_py.crossover import *
import json


class DataSetViewSet(viewsets.ModelViewSet):
    queryset = DataSet.objects.all().order_by('-created')
    serializer_class = DataSetSerializer
class NestedDataSetViewSet(viewsets.ModelViewSet):
    queryset = DataSet.objects.all().order_by('-created')
    serializer_class = NestedDataSetSerializer
class DataPointViewSet(viewsets.ModelViewSet):
    queryset = DataPoint.objects.all().order_by('-created')
    serializer_class = DataPointSerializer
class NestedDataPointViewSet(viewsets.ModelViewSet):
    queryset = DataPoint.objects.all().order_by('-unix_time_millis')
    serializer_class = NestedDataPointSerializer
class DataTypeViewSet(viewsets.ModelViewSet):
    queryset = DataType.objects.all().order_by('-created')
    serializer_class = DataTypeSerializer
class DataValueViewSet(viewsets.ModelViewSet):
    queryset = DataValue.objects.all().order_by('-created')
    serializer_class = DataValueSerializer
class DataUnitViewSet(viewsets.ModelViewSet):
    queryset = DataUnit.objects.all().order_by('-created')
    serializer_class = DataUnitSerializer


@api_view()
def dataSet(
        request, data_set_ids=[0], types="CTDTMP", bounds=[], min_depth=0,
        max_depth=0
):
    result=get_data_set_data(data_set_ids, types, bounds, min_depth, max_depth)
    return Response(result)

@api_view()
def crossover(request, data_set_id=0, types=[]):
    """
    Calculate crossover for this dataset.
    """
    # Always include CTDTMP and SALNTY
    types.extend(['CTDTMP', 'SALNTY', 'CTDSAL'])
    types = list(set(types))
    min_depth = 1000
    dataset = get_data_set_data([data_set_id], types, min_depth=min_depth)
    bounds = dataset_extends(data_set_id)

    ref_ids = DataSet.objects.filter(
            Q(min_lat__lte=bounds[1]) & Q(max_lat__gte=bounds[0]) &
            Q(min_lon__lte=bounds[3]) & Q(max_lon__gte=bounds[2])
    ).values_list('id', flat=True).distinct()
    refdata = get_data_set_data(ref_ids, types, bounds, min_depth)

    for ix,name in enumerate(dataset[0]['data_columns']):
        if name == 'data_point_id':
            idix = ix
        elif name == 'latitude':
            latix = ix
        elif name == 'longitude':
            lonix = ix
        elif name == 'depth':
            depthix = ix
        elif name == 'unix_time_millis':
            timeix = ix
        if name == 'CTDTMP_value':
            tempix = ix
        elif name == 'SALNTY_value':
            sal1ix = ix
        elif name == 'CTDSAL_value':
            sal2ix = ix
        elif name == 'station_number':
            statix = ix
        else:
            crossix = ix

    center_lat = (bounds[0] + bounds[1]) / 2
    center_lon = (bounds[2] + bounds[3]) / 2
    overview = plot_overview_map(dataset, refdata, center_lat=center_lat,
            center_lon=center_lon)
    boundsmap = plot_bounds_map(bounds, dataset, refdata)
    links = []
    path = os.path.dirname(data.__file__)
    for k,m in boundsmap.items():
        l = m + '_merge.png'
        merge_images(path + overview[k], path + m, path + l)
        links.append(l)
        os.remove(path + m)
        os.remove(path + overview[k])
    template = loader.get_template('data/index.html')
    context = {'links': links,}
    return HttpResponse(template.render(context, request))
