import d2qc.data as data
import os.path
import os
import re
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
from d2qc.data.models import *
from d2qc.data.forms import DataFileForm
from rest_framework import viewsets
from d2qc.data.serializers import *
from rest_framework.decorators import api_view
from rest_framework.response import Response
from d2qc.data.sql import *
from lib.d2qc_py.crossover import *
import json


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
                        messages.error(self.request, "ERROR: ".format(str(e)))

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
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

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
        return context

class IndexPage(TemplateView):
    template_name = 'index.html'
