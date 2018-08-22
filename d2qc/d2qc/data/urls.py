from django.urls import path
from django.conf.urls import url, include

from . import views
from d2qc.data.views import *
from d2qc.data.models import *
from rest_framework import routers, serializers, viewsets

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'set', DataSetViewSet)
router.register(r'type', DataTypeViewSet)
router.register(r'point', DataPointViewSet)
router.register(r'value', DataValueViewSet)
router.register(r'unit', DataUnitViewSet)


urlpatterns = [
    url(r'^', include(router.urls)),
]
