import d2qc.data as data
import os.path
import os
import re
from glodap.util import excread
from django.http import HttpResponse
from django.db.models import Max, Min, Count, Q
from django.template import loader
from django.conf import settings
from django.contrib.auth.models import User
from django.views.generic import ListView
from django.views.generic import DetailView
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView
from django.views.generic.edit import UpdateView
from django.views.generic.edit import DeleteView
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.contrib.auth import login
from django.core.cache import cache
from django.utils import timezone
from d2qc.data.models import *
from d2qc.data.forms import DataFileForm
from rest_framework import viewsets
from d2qc.data.serializers import *
from rest_framework.decorators import api_view
from rest_framework.response import Response
from d2qc.data.sql import *
from lib.d2qc_py.crossover import *
from django.contrib.gis.geos import Point
import json
import traceback
import math
import subprocess
from datetime import datetime



def redirect_login(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect('/data')
    else:
        return login(request)

class DataFileViewSet(viewsets.ModelViewSet):

    queryset = DataFile.objects.all()
    serializer_class = DataFileSerializer

class StationViewSet(viewsets.ModelViewSet):

    queryset = Station.objects.all()
    serializer_class = StationSerializer

class CastViewSet(viewsets.ModelViewSet):

    queryset = Cast.objects.all()
    serializer_class = CastSerializer

class DepthViewSet(viewsets.ModelViewSet):

    queryset = Depth.objects.all()
    serializer_class = DepthSerializer

class DataSetViewSet(viewsets.ModelViewSet):

    queryset = DataSet.objects.all().order_by('-created')
    serializer_class = DataSetSerializer

class NestedDataSetViewSet(viewsets.ModelViewSet):

    queryset = DataSet.objects.all().order_by('-created')
    serializer_class = NestedDataSetSerializer

class DataTypeViewSet(viewsets.ModelViewSet):

    queryset = DataType.objects.all().order_by('-created')
    serializer_class = DataTypeSerializer

class DataValueViewSet(viewsets.ModelViewSet):

    queryset = DataValue.objects.all().order_by('-created')
    serializer_class = DataValueSerializer

class DataUnitViewSet(viewsets.ModelViewSet):

    queryset = DataUnit.objects.all().order_by('-created')
    serializer_class = DataUnitSerializer


@api_view()
def dataSet(
        request, data_set_ids=[0], types="CTDTMP", bounds=[], min_depth=0,
        max_depth=0
):
    result=get_data_set_data(data_set_ids, types, bounds, min_depth, max_depth)
    return Response(result)

@api_view()
def crossover(request, data_set_id=0, types=[]):
    """
    Calculate crossover for this dataset.
    """
    # Always include CTDTMP and SALNTY
    types.extend(['temperature', 'salinity'])
    types = list(set(types))
    min_depth = 1000
    dataset = get_data_set_data([data_set_id], types, min_depth=min_depth)
    bounds = dataset_extends(data_set_id)

    ref_ids = DataSet.objects.filter(
            Q(min_lat__lte=bounds[1]) & Q(max_lat__gte=bounds[0]) &
            Q(min_lon__lte=bounds[3]) & Q(max_lon__gte=bounds[2])
    ).values_list('id', flat=True).distinct()
    refdata = get_data_set_data(ref_ids, types, bounds, min_depth)

    for ix,name in enumerate(dataset[0]['data_columns']):
        if name == 'data_point_id':
            idix = ix
        elif name == 'latitude':
            latix = ix
        elif name == 'longitude':
            lonix = ix
        elif name == 'depth':
            depthix = ix
        elif name == 'unix_time_millis':
            timeix = ix
        if name == 'CTDTMP_value':
            tempix = ix
        elif name == 'SALNTY_value':
            sal1ix = ix
        elif name == 'CTDSAL_value':
            sal2ix = ix
        elif name == 'station_number':
            statix = ix
        else:
            crossix = ix

    center_lat = (bounds[0] + bounds[1]) / 2
    center_lon = (bounds[2] + bounds[3]) / 2
    overview = plot_overview_map(dataset, refdata, center_lat=center_lat,
            center_lon=center_lon)
    boundsmap = plot_bounds_map(bounds, dataset, refdata)
    links = []
    path = os.path.dirname(data.__file__)
    for k,m in boundsmap.items():
        l = m + '_merge.png'
        merge_images(path + overview[k], path + m, path + l)
        links.append(l)
        os.remove(path + m)
        os.remove(path + overview[k])
    template = loader.get_template('data/index.html')
    context = {'links': links,}
    return HttpResponse(template.render(context, request))


class DataFileList(ListView):
    model = DataFile
    context_object_name = 'data_file_list'
    def get_queryset(self, *args, **kwargs):
        queryset = DataFile.objects.none()
        if self.request.user.is_authenticated:
            queryset = DataFile.objects.filter(owner_id=self.request.user.id)
        return queryset

class DataFileCreate(CreateView):
    model = DataFile
    form_class = DataFileForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('data_file-detail', kwargs={'pk':self.object.id})

    def form_valid(self, form):
        form.instance.owner = self.request.user
        line_count = 0
        headers = []
        if 'filepath' in self.request.FILES:
            for chunk in self.request.FILES['filepath'].chunks():
                line = ''
                try:
                    chunk = chunk.decode('iso-8859-1')
                except:
                    try:
                        chunk = chunk.decode('utf-8')
                    except Exception as e:
                        messages.error(
                            self.request,
                            "Unknown encoding for file {}".format(
                                str(self.request.FILES['filepath'])
                            )
                        )
                        messages.error(self.request, "ERROR: {}".format(str(e)))

                for line in chunk.splitlines():
                    line_count += 1
                    if line_count > 1 and line.strip()[0] != '#' :
                        break
                    headers.append(line)
                if line_count > 1 and line.strip()[0] != '#' :
                    break
        self.object = form.save(commit=False)
        self.object.headers = "\n".join(headers)
        return super().form_valid(form)

class DataFileUpdate(UpdateView):
    model = DataFile
    fields = ['filepath','name','description','headers']
    def get_success_url(self):
        return reverse('data_file-detail', kwargs={'pk':self.object.id})
    def form_valid(self, form):
        messages.success(
            self.request,
            "Data file {} was updated".format(
                    form.cleaned_data['name']
            )
        )
        return super().form_valid(form)

class DataFileDelete(DeleteView):
    model = DataFile
    success_url = reverse_lazy('data_file-list')
    def delete(self, request, *args, **kwargs):
        rex = re.compile('^[a-zA-Z_/]+delete/([0-9]+)')
        messages.success(
            self.request,
            "Data file #{} was deleted".format(
                    rex.findall(request.path)[0]
            )
        )
        return super().delete(request, *args, **kwargs)

class DataFileDetail(DetailView):
    model = DataFile
    exec = False
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fileobject = DataFile.objects.get(pk=self.kwargs.get('pk'))
        context['import_mode'] = self.request.path.endswith('import')
        # Load data_file owner data:
        try:
            owner = User.objects.get(pk=context['object'].owner_id)
            context['owner'] = {
                    'username': owner.username,
                    'first_name': owner.first_name,
                    'last_name': owner.last_name,
            }
        except:
            pass

        # Load file head:
        filecontent = ""
        try:
            filecontent = fileobject.read_file()
        except Exception as err:
            messages.error(
                    self.request,
                    'Could not read file {}'.format(
                            fileobject.filepath
                    )
            )
            messages.error(self.request, 'ERROR: {}'.format(str(err)))

        context['filehead'] = filecontent[:50]
        context['count'] = len(filecontent)

        if self.exec and not fileobject.import_started:
            # Spawn process to start importing file data
            subprocess.Popen([
                settings.PYTHON_ENV,
                os.path.join(settings.BASE_DIR,"manage.py"),
                'import_exc_file',
                str(fileobject.id),
                '-v',
                '0'
            ])
        context['import_time'] = ''
        if fileobject.import_finnished:
            context['import_time'] = (
                fileobject.import_finnished -
                fileobject.import_started
            ).total_seconds()

        return context


class IndexPage(TemplateView):
    template_name = 'index.html'

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

class ProfileUpdate(UpdateView):
    model = Profile
    fields = ['min_depth','crossover_radius']
    def get_success_url(self):
        return reverse('data')
    def get_object(self):
        try:
            return self.request.user.profile
        except:
            self.request.user.profile = Profile(user=self.request.user)
            self.request.user.save()
        return self.request.user.profile

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(
            self.request,
            "Profile settings updated"
        )
        return super().form_valid(form)
