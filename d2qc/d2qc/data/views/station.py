from rest_framework import viewsets

from d2qc.data.models import Station
from d2qc.data.serializers import StationSerializer


class StationViewSet(viewsets.ModelViewSet):

    queryset = Station.objects.all()
    serializer_class = StationSerializer
