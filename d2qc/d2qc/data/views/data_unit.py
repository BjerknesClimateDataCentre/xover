from rest_framework import viewsets

from d2qc.data.models import DataUnit
from d2qc.data.serializers import DataUnitSerializer


class DataUnitViewSet(viewsets.ModelViewSet):

    queryset = DataUnit.objects.all().order_by('-created')
    serializer_class = DataUnitSerializer
