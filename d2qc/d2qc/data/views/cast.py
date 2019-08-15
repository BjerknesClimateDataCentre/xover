from rest_framework import viewsets

from d2qc.data.models import Cast
from d2qc.data.serializers import CastSerializer


class CastViewSet(viewsets.ModelViewSet):

    queryset = Cast.objects.all()
    serializer_class = CastSerializer
