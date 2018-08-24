from django.shortcuts import render
from django.http import HttpResponse
from d2qc.data.models import DataSet, DataPoint, DataType, DataValue, DataUnit
from rest_framework import viewsets
from d2qc.data.serializers import *
from rest_framework.decorators import api_view
from rest_framework.response import Response


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
