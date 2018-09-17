from django.http import HttpResponse
from django.db.models import Max, Min, Count, Q
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
def crossover(request, data_set_id=0, types=""):
    """
    Calculate crossover for this dataset.
    """

    min_depth = 1000
    dataset = get_data_set_data([data_set_id], types, min_depth=min_depth)
    bounds = dataset_extends(data_set_id)

    ref_ids = DataSet.objects.filter(
            Q(min_lat__lte=bounds[1]) & Q(max_lat__gte=bounds[0]) &
            Q(min_lon__lte=bounds[3]) & Q(max_lon__gte=bounds[2])
    ).values_list('id', flat=True).distinct()
    refdata = get_data_set_data(ref_ids, types, bounds, min_depth)


    #dataset = dataset.filter(points.lat)
    # print(refdata)
    #print(dataset[1].id)
    #refs = DataSet.objects.filter()
    return Response(dataset)
