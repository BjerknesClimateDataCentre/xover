from django.shortcuts import render
from django.http import HttpResponse
from d2qc.data.models import DataSet, DataPoint, DataType, DataValue
from rest_framework import viewsets
from d2qc.data.serializers import *


class DataSetViewSet(viewsets.ModelViewSet):
    queryset = DataSet.objects.all().order_by('-created')
    serializer_class = DataSetSerializer
class DataPointViewSet(viewsets.ModelViewSet):
    queryset = DataPoint.objects.all().order_by('-created')
    serializer_class = DataPointSerializer
class DataTypeViewSet(viewsets.ModelViewSet):
    queryset = DataType.objects.all().order_by('-created')
    serializer_class = DataTypeSerializer
class DataValueViewSet(viewsets.ModelViewSet):
    queryset = DataValue.objects.all().order_by('-created')
    serializer_class = DataValueSerializer
