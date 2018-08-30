from django.urls import path, register_converter
from django.conf.urls import url, include

from . import views
from d2qc.data.views import *
from d2qc.data.models import *
from d2qc.urlconverters import *
from rest_framework import routers, serializers, viewsets

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'set', DataSetViewSet)
router.register(r'nested/set', NestedDataSetViewSet)
router.register(r'type', DataTypeViewSet)
router.register(r'point', DataPointViewSet)
router.register(r'nested/point', NestedDataPointViewSet)
router.register(r'value', DataValueViewSet)
router.register(r'unit', DataUnitViewSet)

register_converter(DataTypeConverter, 'datatypes')



urlpatterns = [
    path('join/dataset/<int:data_set_id>/<datatypes:types>', views.dataSet),
    path('join/dataset/<int:data_set_id>', views.dataSet),
    path('join/dataset/', views.dataSet),
    url(r'^', include(router.urls)),
]
