from rest_framework import viewsets

from d2qc.data.models import DataSet
from d2qc.data.serializers import DataSetSerializer
from d2qc.data.serializers import NestedDataSetSerializer

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.urls import reverse_lazy
from django.views.generic import ListView
from django.views.generic import DetailView
from django.views.generic.edit import DeleteView

import subprocess
import os
import re


class DataSetViewSet(viewsets.ModelViewSet):

    queryset = DataSet.objects.all().order_by('-created')
    serializer_class = DataSetSerializer

class NestedDataSetViewSet(viewsets.ModelViewSet):

    queryset = DataSet.objects.all().order_by('-created')
    serializer_class = NestedDataSetSerializer


class DataSetList(ListView):
    model = DataSet
    context_object_name = 'data_set_list'
    def get_queryset(self, *args, **kwargs):
        queryset = DataSet.objects.none()
        if self.request.user.is_authenticated:
            queryset = DataSet.objects.filter(owner_id=self.request.user.id)
        return queryset

class DataSetDetail(DetailView):
    model = DataSet
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data_set = self.get_object()
        context['data_types'] = data_set.get_data_types(
            min_depth = data_set.owner.profile.min_depth
        )
        for data_type in context['data_types']:
            if data_type['id'] == self.kwargs.get('parameter_id'):
                context['parameter'] = data_type
                break

        # Get the stations for the current data set,
        # filtering by parameter if required
        data_set_stations = data_set.get_stations(
            parameter_id=self.kwargs.get('parameter_id')
        )

        # Get the station buffer outline polygon
        context['stations_polygon'] = data_set.get_stations_polygon(
            data_set_stations
        )

        # Get the positions of the data set stations
        context['station_positions'] = data_set.get_station_positions(
            data_set_stations
        )

        if not context['stations_polygon']:
            context['stations_polygon'] = ''
        context['dataset_profiles'] = '[]'
        context['dataset_interp_profiles'] = '[]'
        context['dataset_ref_profiles'] = '[]'
        context['dataset_ref_interp_profiles'] = '[]'
        if self.kwargs.get('parameter_id'):
            cache_key_px = "_xover-{}-{}-{}-{}".format(
                data_set.id,
                self.kwargs.get('parameter_id'),
                data_set.owner.profile.crossover_radius,
                data_set.owner.profile.min_depth,
            )

            # Check if calculation has begun
            calculating_key = 'calculating' + cache_key_px
            calculating_value = cache.get(calculating_key, False)

            # Check if calculation is ready
            ready_key = 'calculate' + cache_key_px
            value = cache.get(ready_key, False)
            context['summary_stats'] = None
            if calculating_value is False:
                # Spawn process to calculate weighted mean for parameter
                subprocess.Popen([
                    settings.PYTHON_ENV,
                    os.path.join(settings.BASE_DIR,"manage.py"),
                    'calculate_xover',
                    str(data_set.id),
                    str(self.kwargs.get('parameter_id')),
                    str(data_set.owner.profile.crossover_radius),
                    str(data_set.owner.profile.min_depth),
                ])
                cache.set(calculating_key, True)
            elif value is not False:
                context['summary_stats'] = value

            # Get the crossover stations, restricted to a specific dataset
            # if crossover_data_set_id is not None
            crossover_stations = data_set.get_crossover_stations(
                stations=data_set_stations,
                parameter_id=self.kwargs.get('parameter_id'),
                crossover_data_set_id=self.kwargs.get('data_set_id')
            )

            # Get the positions of the crossover stations
            context['crossover_positions'] = data_set.get_station_positions(
                crossover_stations
            )

            # Get the data set details of the crossovers
            context['crossover_datasets'] = data_set.get_station_data_sets(
                data_set.get_crossover_stations(
                    stations=data_set_stations,
                    parameter_id=self.kwargs.get('parameter_id')
                )
            )

            # If we are only looking at one crossover data set,
            # restrict the main data set to only those stations
            # within range of that crossover
            if self.kwargs.get('data_set_id') is not None:
                context['crossover_data_set_id'] = self.kwargs.get('data_set_id')
                data_set_stations = data_set.get_crossover_stations(
                    data_set_id=self.kwargs.get('data_set_id'),
                    stations=crossover_stations,
                    parameter_id=self.kwargs.get('parameter_id'),
                    crossover_data_set_id=self.kwargs.get('pk')
                )

                context['station_positions'] = data_set.get_station_positions(
                    data_set_stations
                )

                context['stations_polygon'] = data_set.get_stations_polygon(
                    data_set_stations
                )

            # Get the profiles for the plot
            context['dataset_profiles'] = data_set.get_profiles_as_json(
                data_set.get_profiles_data(
                    data_set_stations,
                    self.kwargs.get('parameter_id'),
                )
            )
            context['dataset_interp_profiles'] = data_set.get_profiles_as_json(
                data_set.get_interp_profiles(
                    data_set_stations,
                    self.kwargs.get('parameter_id'),
                )
            )
            context['dataset_stats'] = {}
            if self.kwargs.get('data_set_id') is not None:
                profile_stations = data_set_stations
                context['dataset_ref_profiles'] = data_set.get_profiles_as_json(
                    data_set.get_profiles_data(
                        crossover_stations,
                        self.kwargs.get('parameter_id'),
                    )
                )
                context['dataset_ref_interp_profiles'] = data_set.get_profiles_as_json(
                    data_set.get_interp_profiles(
                        crossover_stations,
                        self.kwargs.get('parameter_id'),
                    )
                )
                stats = data_set.get_profiles_stats(
                    data_set_stations,
                    crossover_stations,
                    self.kwargs.get('parameter_id'),
                )
                context['dataset_stats'] = json.dumps(stats, allow_nan=False)

        return context

class DataSetDelete(DeleteView):
    model = DataSet
    success_url = reverse_lazy('data_set-list')
    def delete(self, request, *args, **kwargs):
        rex = re.compile('^[a-zA-Z_/]+delete/([0-9]+)')

        data_file = self.model.objects.get(pk=kwargs['pk']).data_file
        messages.success(
            self.request,
            "Data set #{} was deleted".format(kwargs['pk'])
        )
        retval = super().delete(request, *args, **kwargs)
        data_file.import_started = None
        data_file.import_finnished = None
        data_file.save()
        return retval