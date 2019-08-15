from rest_framework import viewsets

from d2qc.data.models import DataValue
from d2qc.data.serializers import DataValueSerializer


class DataValueViewSet(viewsets.ModelViewSet):

    queryset = DataValue.objects.all().order_by('-created')
    serializer_class = DataValueSerializer
