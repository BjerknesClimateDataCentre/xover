from rest_framework import viewsets

from d2qc.data.models import DataType
from d2qc.data.serializers import DataTypeSerializer


class DataTypeViewSet(viewsets.ModelViewSet):

    queryset = DataType.objects.all().order_by('-created')
    serializer_class = DataTypeSerializer
