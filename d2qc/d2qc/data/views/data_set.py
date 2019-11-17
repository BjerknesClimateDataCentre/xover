from rest_framework import viewsets

import glodap.util.stats as stats

from d2qc.data.models import DataSet, DataTypeName, DataType, Operation
from d2qc.data.serializers import DataSetSerializer
from d2qc.data.serializers import NestedDataSetSerializer
from d2qc.data.forms import MergeForm, NormalizeForm
from d2qc.data.forms import MergeProfileForm, DataSetDetailsProfileForm

from django import forms
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.urls import reverse_lazy
from django.urls import reverse
from django.views import View
from django.views.generic import ListView
from django.views.generic import DetailView
from django.views.generic import DeleteView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic import FormView

import json
import os
import re
import subprocess
import pandas as pd


class MenuMixin:
    ALKALINITY = 'SDN:P01::ALKYZZXX'
    CO2 = 'SDN:P01::PCO2XXXX'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_normalizable'] = (
            True if self.object.getNormalizableParameters(
                self.request.user.profile
            ) else False
        )
        context['has_operations'] = self.object.operations.exists()
        return context


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

class DataSetDetail(MenuMixin, DetailView,):
    model = DataSet
    profile_form = None
    template_name = 'data/dataset_detail/detail.html'

    def post(self, request, *args, **kwargs):
        if request.POST.get('replot_with_options', False):
            self.profile_form = DataSetDetailsProfileForm(
                request.POST,
                instance = request.user.profile,
            )
            if self.profile_form.is_valid():
                self.profile_form.save()

        return self.get(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if not self.profile_form:
            self.profile_form = DataSetDetailsProfileForm(instance = request.user.profile)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data_set = self.get_object()
        crossover_radius = self.request.user.profile.crossover_radius
        min_depth = self.request.user.profile.min_depth
        only_qc_controlled_data = self.request.user.profile.only_qc_controlled_data
        context['profile_form'] = self.profile_form
        context['xtype'] = self.request.user.profile.depth_metric
        context['data_type_names'] = data_set.get_data_type_names(
            min_depth = self.request.user.profile.min_depth,
            only_qc_controlled_data = only_qc_controlled_data,
        )
        for data_type_name in context['data_type_names']:
            if data_type_name['id'] == self.kwargs.get('parameter_id'):
                context['parameter'] = data_type_name
                break
        merge_form = MergeForm(data_type_names=context['data_type_names'])
        context['merge_form'] = merge_form
        # Get stations positions and polygons for the whole cruise
        cruise_stations = data_set.get_stations(
            crossover_radius = crossover_radius,
            min_depth = min_depth,
            only_qc_controlled_data = only_qc_controlled_data,
        )
        context['cruise_polygon'] = data_set.get_stations_polygon(
            cruise_stations,
            crossover_radius = crossover_radius,
        )
        context['cruise_positions'] = data_set.get_station_positions(
            cruise_stations
        )

        # Get the stations for the current data set,
        # filtering by parameter if required
        data_set_stations = data_set.get_stations(
            parameter_id=self.kwargs.get('parameter_id'),
            crossover_radius = crossover_radius,
            min_depth = min_depth,
            only_qc_controlled_data = only_qc_controlled_data,
        )

        # Get the station buffer outline polygon
        context['stations_polygon'] = data_set.get_stations_polygon(
            data_set_stations,
            crossover_radius = crossover_radius,
        )

        # Get the positions of the data set stations

        if not context['stations_polygon']:
            context['stations_polygon'] = ''
        context['dataset_profiles'] = None
        context['dataset_interp_profiles'] = None
        context['dataset_ref_profiles'] = None
        context['dataset_ref_interp_profiles'] = None
        minimum_num_stations = 3

        if not self.kwargs.get('data_set_id'):
            context['station_positions'] = data_set.get_station_positions(
                data_set_stations
            )

        if self.kwargs.get('parameter_id'):
            cache_key_px = "_xover-{}-{}-{}-{}-{}-{}-{}".format(
                data_set.id,
                self.kwargs.get('parameter_id'),
                self.request.user.profile.crossover_radius,
                self.request.user.profile.min_depth,
                minimum_num_stations,
                self.request.user.profile.depth_metric,
                only_qc_controlled_data,
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
                args = [
                    settings.PYTHON_ENV,
                    os.path.join(settings.BASE_DIR,"manage.py"),
                    'calculate_xover',
                    str(data_set.id),
                    str(self.kwargs.get('parameter_id')),
                    str(self.request.user.profile.crossover_radius),
                    str(self.request.user.profile.min_depth),
                    self.request.user.profile.depth_metric,
                    '--minimum_num_stations', str(minimum_num_stations),
                ]
                if only_qc_controlled_data:
                    args.append('--only_qc_controlled_data')
                subprocess.Popen(args)
                cache.set(calculating_key, True)
            elif value is not False:
                context['summary_stats'] = value

            # Get the crossover stations, restricted to a specific dataset
            # if crossover_data_set_id is not None
            crossover_stations = data_set.get_crossover_stations(
                stations=data_set_stations,
                parameter_id=self.kwargs.get('parameter_id'),
                crossover_data_set_id=self.kwargs.get('data_set_id'),
                crossover_radius = crossover_radius,
                min_depth = min_depth,
                only_qc_controlled_data = only_qc_controlled_data,
            )

            # Get the positions of the crossover stations
            context['crossover_positions'] = data_set.get_station_positions(
                crossover_stations
            )

            # Get the data set details of the crossovers
            context['crossover_datasets'] = data_set.get_station_data_sets(
                data_set.get_crossover_stations(
                    stations=data_set_stations,
                    parameter_id=self.kwargs.get('parameter_id'),
                    minimum_num_stations = 3,
                    crossover_radius = crossover_radius,
                    min_depth = min_depth,
                    only_qc_controlled_data = only_qc_controlled_data,
                )
            )

            # If we are only looking at one crossover data set,
            # restrict the main data set to only those stations
            # within range of that crossover
            if self.kwargs.get('data_set_id'):
                context['data_set_id'] = self.kwargs.get('data_set_id')
                context['crossover_data_set_id'] = self.kwargs.get('data_set_id')
                context['crossover_expocode'] = DataSet.objects.get(
                    pk = self.kwargs.get('data_set_id')
                )
                data_set_stations = data_set.get_crossover_stations(
                    data_set_id=self.kwargs.get('data_set_id'),
                    stations=crossover_stations,
                    parameter_id=self.kwargs.get('parameter_id'),
                    crossover_data_set_id=self.kwargs.get('pk'),
                    crossover_radius = crossover_radius,
                    min_depth = min_depth,
                    only_qc_controlled_data = only_qc_controlled_data,
                )

                context['station_positions'] = data_set.get_station_positions(
                    data_set_stations
                )

                context['stations_polygon'] = data_set.get_stations_polygon(
                    data_set_stations,
                    crossover_radius = crossover_radius,
                )

            # Get the profiles for the plot
            context['dataset_profiles'] = data_set.get_profiles_as_json(
                data_set.get_profiles_data(
                    data_set_stations,
                    self.kwargs.get('parameter_id'),
                    only_this_parameter = True,
                    min_depth = min_depth,
                    only_qc_controlled_data = only_qc_controlled_data,
                ),
                xtype = self.request.user.profile.depth_metric,
            )
            context['dataset_interp_profiles'] = data_set.get_profiles_as_json(
                data_set.get_interp_profiles(
                    data_set_stations,
                    self.kwargs.get('parameter_id'),
                    min_depth = min_depth,
                    xtype = self.request.user.profile.depth_metric,
                    only_qc_controlled_data = only_qc_controlled_data,
                ),
                xtype = self.request.user.profile.depth_metric,
            )
            context['dataset_stats'] = {}
            if self.kwargs.get('data_set_id') is not None:
                profile_stations = data_set_stations
                context['dataset_ref_profiles'] = data_set.get_profiles_as_json(
                    data_set.get_profiles_data(
                        crossover_stations,
                        self.kwargs.get('parameter_id'),
                        min_depth = min_depth,
                        only_qc_controlled_data = only_qc_controlled_data,
                    ),
                    self.request.user.profile.depth_metric,
                )
                context['dataset_ref_interp_profiles'] = data_set.get_profiles_as_json(
                    data_set.get_interp_profiles(
                        crossover_stations,
                        self.kwargs.get('parameter_id'),
                        min_depth = min_depth,
                        xtype = self.request.user.profile.depth_metric,
                        only_qc_controlled_data = only_qc_controlled_data,
                    ),
                    xtype = self.request.user.profile.depth_metric,
                )
                stats = data_set.get_profiles_stats(
                    data_set_stations,
                    crossover_stations,
                    self.kwargs.get('parameter_id'),
                    min_depth = min_depth,
                    crossover_radius = crossover_radius,
                    xtype = self.request.user.profile.depth_metric,
                    only_qc_controlled_data = only_qc_controlled_data,
                )
                if stats:
                    context['dataset_stats'] = json.dumps(stats, allow_nan=False)
        return context

class DataSetDelete(DeleteView):
    model = DataSet
    success_url = reverse_lazy('data_set-list')

    def delete(self, request, *args, **kwargs):
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

class DataSetMerge(MenuMixin, DetailView,):
    model = DataSet
    template_name = 'data/dataset_detail/dataset_merge.html'
    profile_form = None
    merge_form = None

    def post(self, request, *args, **kwargs):
        data_set = self.get_object()
        if request.POST.get('replot_with_options', False):
            self.profile_form = MergeProfileForm(
                request.POST,
                instance = request.user.profile
            )
            if self.profile_form.is_valid():
                self.profile_form.save()
        else:
            self.profile_form = MergeProfileForm(instance=request.user.profile)

        only_qc_controlled_data = request.user.profile.only_qc_controlled_data
        data_type_names = data_set.get_data_type_names(
            min_depth = request.user.profile.min_depth,
            only_qc_controlled_data = only_qc_controlled_data,
        )
        if request.POST.get('save_parameters'):
            self.merge_form = MergeForm(
                request.POST,
                data_type_names = data_type_names,
            )
            if self.merge_form.is_valid():
                self.merge_form.save_merge_data(data_set = self.get_object())
                # Reloading this to get the new, inserted merge parameter
                self.merge_form = MergeForm(
                    request.POST,
                    data_type_names = data_set.get_data_type_names(
                        min_depth = request.user.profile.min_depth,
                        only_qc_controlled_data = only_qc_controlled_data,
                    ),
                )
        elif request.POST.get('plot_parameters'):
            self.merge_form = MergeForm(
                request.POST,
                data_type_names = data_type_names,
            )
        else:
            self.merge_form = MergeForm(
                data_type_names = data_type_names,
            )

        retval = super().get(request, *args, **kwargs)
        return retval

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data_set = self.get_object()

        only_qc_controlled_data = (
            self.request.user.profile.only_qc_controlled_data
        )

        xtype = self.request.user.profile.depth_metric
        context['profile_form'] = self.profile_form

        context['data_type_names'] = data_set.get_data_type_names(
            min_depth = self.request.user.profile.min_depth,
            only_qc_controlled_data = only_qc_controlled_data,
        )
        if self.merge_form and self.merge_form.is_valid():
            merge = data_set.get_merge_data(
                self.merge_form.cleaned_data['primary'],
                self.merge_form.cleaned_data['secondary'],
                min_depth = self.merge_form.cleaned_data['merge_min_depth'],
                only_qc_controlled_data = only_qc_controlled_data,
            )
            primary_type = DataTypeName.objects.get(
                pk=self.merge_form.cleaned_data['primary']
            )
            secondary_type = DataTypeName.objects.get(
                pk=self.merge_form.cleaned_data['secondary']
            )
            merge = merge.replace({pd.np.nan: None})
            slope, intercept = stats.linear_fit(
                merge['primary'].tolist(),
                merge['secondary'].tolist(),
            )

            data = {
                'depth': merge['depth'].tolist(),
                'diff': merge['diff'].tolist(),
                'primary': merge['primary'].tolist(),
                'secondary': merge['secondary'].tolist(),
                'primary_type': {
                    'label': primary_type.name,
                },
                'secondary_type': {
                    'label': secondary_type.name,
                },
            }
            context['merge_data'] = json.dumps(data)
            context['slope'] = slope
            context['intercept'] = intercept
        context['merge_form'] = self.merge_form
        return context

class DataSetNormalization(
    MenuMixin,
    FormView,
    SingleObjectMixin,
):
    model = DataSet
    template_name = 'data/dataset_detail/dataset_normalize.html'
    form_class = NormalizeForm
    is_normalizable = False
    success_url = None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['data_set_id'] = self.object.id
        profile = self.request.user.profile
        kwargs['params_opts'] = self.object.getNormalizableParameters(
            self.request.user.profile
        )
        if kwargs['params_opts']:
            self.is_normalizable = True
        return kwargs

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        retval = super().post(request, *args, **kwargs)
        return retval

    def form_valid(self, form):
        self.success_url = reverse('data_set_normalize', args=[self.object.id])
        retval = super().form_valid(form)
        if retval:
            saved_data = form.save_normalization_data(
                self.object,
                self.request.user
            )
            if saved_data:
                messages.success(
                    self.request,
                    "Normalized variables for data set: {}".format(
                        ', '.join([
                            f"{r['name']}=>{r['norm_name']}" for r in saved_data
                        ])
                    )
                )

        return retval

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class OperationList(MenuMixin, ListView):
    model = Operation
    context_object_name = 'operation_list'
    template_name = 'data/dataset_detail/operation_list.html'

    def get(self, request, *args, **kwargs):
        self.object = DataSet.objects.get(pk=kwargs['pk'])
        return super().get(request, *args, **kwargs)

    def get_queryset(self, *args, **kwargs):
        queryset = Operation.objects.none()
        if self.request.user.is_authenticated:
            queryset = Operation.objects.filter(data_set=self.object)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object'] = self.object
        return context
