from django.shortcuts import render
from django.http import HttpResponse
from d2qc.data.models import DataSet, DataPoint, DataType, DataValue, DataUnit
from rest_framework import viewsets
from d2qc.data.serializers import *
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import connection
import re


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
    queryset = DataPoint.objects.all().order_by('-created')
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
def dataSet(request, data_set_id=0, types=""):
    cursor = connection.cursor()
    cursor.execute('SELECT ds.id, ds.expocode FROM d2qc_datasets ds WHERE id=%s', [data_set_id])
    columns = [col[0] for col in cursor.description]
    result = dict(zip(columns, cursor.fetchone()))

    sql = "SELECT dp.id, dp.latitude, dp.longitude, dp.depth"
    sql += ", dp.unix_time_millis"
    frm = " FROM d2qc_datapoints dp "
    join = ""
    where = " WHERE dp.data_set_id = %s"
    if len(types) > 0:
        for type in types:
            px = re.sub('[^a-zA-Z]', '', type)
            sql   += ", {}.value AS {}_value".format(px, px)
            join  += " INNER JOIN d2qc_datavalues {}".format(px)
            join  += " ON (dp.id = {}.data_point_id)".format(px)
            join  += " INNER JOIN d2qc_datatypes dt_{}".format(px)
            join  += " ON (dt_{}.id = {}.data_type_id)".format(px, px)
            where += " AND dt_{}.original_label = '{}'".format(px, type)
    cursor.execute(sql + frm + join + where, [data_set_id])
    result['data_columns'] = [col[0] for col in cursor.description]
    result['data_points'] = cursor.fetchall()

    return Response(result)
