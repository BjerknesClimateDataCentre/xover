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
register_converter(LatLonBoundsConverter, 'bounds')
register_converter(NumberListConverter, 'numbers')

px = 'join/dataset'
ids = '/<numbers:data_set_ids>'
types = '/<datatypes:types>'
bounds = '/<bounds:bounds>'
min_depth = '/<int:min_depth>'
max_depth = '/<int:max_depth>'
urlpatterns = [
    path(px + ids, views.dataSet),
    path(px + ids + types, views.dataSet),
    path(px + ids + types + bounds, views.dataSet),
    path(px + ids + types + bounds + min_depth, views.dataSet),
    path(px + ids + types + bounds + min_depth + max_depth, views.dataSet),
    path(px + ids + types + min_depth, views.dataSet),
    path(px + ids + types + min_depth + max_depth, views.dataSet),
    path('crossover/<int:data_set_id>/<datatypes:types>', views.crossover),
    url(r'^', include(router.urls)),
]
