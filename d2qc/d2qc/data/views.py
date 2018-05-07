from django.shortcuts import render
from django.http import HttpResponse
from d2qc.data.models import DataSet
from rest_framework import viewsets
from d2qc.data.serializers import DataSetSerializer


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")

class DataSetViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Data Sets to be viewed or edited.
    """
    queryset = DataSet.objects.all().order_by('-created')
    serializer_class = DataSetSerializer
