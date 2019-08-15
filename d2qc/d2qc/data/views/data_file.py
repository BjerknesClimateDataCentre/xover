import os
import re
import subprocess

from rest_framework import viewsets

from d2qc.data.serializers import DataFileSerializer
from d2qc.data.models import DataFile
from d2qc.data.forms import DataFileForm

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView
from django.views.generic import DetailView
from django.views.generic.edit import CreateView
from django.views.generic.edit import UpdateView
from django.views.generic.edit import DeleteView

class DataFileViewSet(viewsets.ModelViewSet):

    queryset = DataFile.objects.all()
    serializer_class = DataFileSerializer

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
        file = self.get_object()
        if file.data_sets:
            data_sets = []
            for d in file.data_sets.all():
                ds = '<a href="{}">{}</a>'.format(
                    reverse('data_set-detail', args=[d.id]),
                    d.expocode,
                )
                data_sets.append(ds)
            messages.error(
                self.request,
                "Cannot delete file before deleting dataset(s) {}.".format(
                    ', '.join(data_sets)
                )
            )
            return redirect(reverse('data_file-detail', args=[kwargs['pk']]))

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
