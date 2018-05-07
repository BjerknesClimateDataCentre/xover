from django.urls import path

from . import views
from d2qc.data.views import DataSetViewSet
from d2qc.data.models import *
from rest_framework import routers, serializers, viewsets

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'data', DataSetViewSet)


urlpatterns = [
    path('', views.index, name='index'),
]
