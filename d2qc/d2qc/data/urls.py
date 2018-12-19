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
router.register(r'station', StationViewSet)
router.register(r'cast', CastViewSet)
router.register(r'dept', DepthViewSet)
router.register(r'value', DataValueViewSet)
router.register(r'unit', DataUnitViewSet)
router.register(r'file', DataFileViewSet)

register_converter(DataTypeConverter, 'datatypes')
register_converter(LatLonBoundsConverter, 'bounds')
register_converter(NumberListConverter, 'numbers')

px = 'join/dataset'
cx = 'crossover'
ids = '/<numbers:data_set_ids>'
id = '/<int:data_set_id>'
types = '/<datatypes:types>'
bounds = '/<bounds:bounds>'
min_depth = '/<int:min_depth>'
max_depth = '/<int:max_depth>'
file = 'data_file'
add = '/add/'
detail = '/detail'
update = '/update'
delete = '/delete'
urlpatterns = [
    path(px + ids, views.dataSet),
    path(px + ids + types, views.dataSet),
    path(px + ids + types + bounds, views.dataSet),
    path(px + ids + types + bounds + min_depth, views.dataSet),
    path(px + ids + types + bounds + min_depth + max_depth, views.dataSet),
    path(px + ids + types + min_depth, views.dataSet),
    path(px + ids + types + min_depth + max_depth, views.dataSet),
    path(cx + id + types, views.crossover),
    #url(r'^', include(router.urls)),
    path(
            file + detail + '/<int:pk>/',
            DataFileDetail.as_view(),
            name='data_file-detail'
    ),
    path(
            file + update + '/<int:pk>/',
            DataFileUpdate.as_view(),
            name='data_file-update'
    ),
    path(
            file + '/',
            DataFileList.as_view(),
            name='data_file-list'
    ),
    path(
            file + add,
            DataFileCreate.as_view(),
            name='data_file-create'
    ),
    path(
            file + delete + '/<int:pk>',
            DataFileDelete.as_view(),
            name='data_file-delete'
    ),
    path(
            '',
            IndexPage.as_view(),
            name='data'
    ),
]
