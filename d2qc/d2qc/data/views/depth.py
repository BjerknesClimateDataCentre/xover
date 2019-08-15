from rest_framework import viewsets

from d2qc.data.models import Depth
from d2qc.data.serializers import DepthSerializer


class DepthViewSet(viewsets.ModelViewSet):

    queryset = Depth.objects.all()
    serializer_class = DepthSerializer
