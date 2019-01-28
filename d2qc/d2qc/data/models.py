from django.contrib.gis.db import models
from django.forms import ModelForm
from django.contrib.auth.models import User
from django.conf import settings
import os.path
import datetime
import logging
import re
from decimal import Decimal
import math
from django.db import connection


class Profile(models.Model):
    class Meta:
        db_table = 'd2qc_user_profile'
    user = models.OneToOneField(
        User,
        related_name='profile',
        on_delete = models.CASCADE,
        blank=True,
        null=True,
        editable=False
    )
    min_depth = models.IntegerField(default=1500)
    crossover_radius = models.IntegerField(default=200000)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

class DataFile(models.Model):
    class Meta:
        db_table = 'd2qc_data_files'

    # Make sure files get unique filenames
    def file_store_path(self, filename):
        # clear filename of illegal characters
        filename = re.sub('[^a-zA-Z0-9\.\-\_]', '', filename)
        id = self.owner.id
        path = os.path.join(
                settings.DATA_FOLDER,
                'UID_{}'.format(id)
        )
        i = 0
        name = '{}__{}'.format(i, filename)
        while os.path.isfile(os.path.join(path, name)):
            i += 1
            name = '{}__{}'.format(i, filename)
        return os.path.join(path, name)

    id = models.AutoField(primary_key=True)
    filepath = models.FileField(
            upload_to=file_store_path,
            blank=True,
            null=True
    )
    name = models.CharField(max_length=255, blank=True)
    description = models.CharField(max_length=255, blank=True)
    headers = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(
            User,
            on_delete = models.PROTECT,
            blank=True,
            null=True,
            editable=False
    )

    def __str__(self):
        return self.name if self.name else self.filepath

    # Delete files as object is deleted
    def delete(self):
        # Dont delete file if file has related data set(s)
        if not DataSet.objects.filter(data_file_id=self.id).exists():
            self.filepath.delete()
        super().delete()

    def is_imported(self):
        return self.data_sets.count() > 0

    def read_file(self):
        filearray = []
        if self.filepath:
            path = os.path.join(
                settings.BASE_DIR,
                str(self.filepath),
            )
            try:
                with open(path, encoding="utf-8") as excfile:
                    filearray = excfile.readlines()
            except:
                try:
                    with open(path, encoding="iso-8859-1") as excfile:
                        filearray = excfile.readlines()
                except:
                    messages.error(
                            self.request,
                            'Could not read file {}'.format(
                                    path
                            )
                    )
                    messages.error(self.request, 'ERROR: {}'.format(str(err)))
        return filearray



class DataSet(models.Model):
    class Meta:
        db_table = 'd2qc_data_sets'
        ordering = ['expocode']
        unique_together = ('expocode', 'owner')
    _datatypes = {}

    id = models.AutoField(primary_key=True)
    is_reference = models.BooleanField(default=False)
    expocode = models.CharField(max_length=255)
    data_file = models.ForeignKey(
        'DataFile',
        related_name='data_sets',
        on_delete = models.PROTECT,
        blank=True,
        null=True
    )
    owner = models.ForeignKey(
            User,
            on_delete = models.PROTECT,
            blank=True,
            null=True,
            editable=False
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.expocode

    def get_data_types(self):
        """Fetch all data types in this data set from the database"""

        # If this has been called before:
        if self._datatypes:
            return self._datatypes

        sql = """select distinct dt.original_label, dt.identifier, dt.id
            from d2qc_data_types dt
            inner join d2qc_data_values dv on dv.data_type_id = dt.id
            inner join d2qc_depths d on d.id=dv.depth_id
            inner join d2qc_casts c on c.id=d.cast_id
            inner join d2qc_stations s on c.station_id=s.id
            where s.data_set_id = {}
            order by dt.original_label;""".format(self.id)

        cursor = connection.cursor()
        cursor.execute(sql)
        typelist = [{
            'original_label': type[0],
            'identifier': type[1],
            'id': type[2],
        } for type in cursor.fetchall()]
        self._datatypes = typelist
        return typelist

    def get_stations(self, parameter_id = None):
        """Get the stations in the data set"""

        sql = """select st_astext(st_collect(position))
                from d2qc_stations
                where data_set_id={};""".format(self.id)
        if parameter_id:
            sql = """select st_astext(st_collect(points.position)) from
                (select distinct s.id, position
                from d2qc_stations s
                inner join d2qc_casts c on c.station_id = s.id
                inner join d2qc_depths d on d.cast_id = c.id
                inner join d2qc_data_values dv on dv.depth_id = d.id
                where data_set_id={}
                and dv.data_type_id={}) points
                """.format(self.id, parameter_id)

        cursor = connection.cursor()
        cursor.execute(sql)
        return cursor.fetchall()[0][0]

    def get_crossover_stations(self, parameter_id):
        stations = """
            select distinct s.position
            from d2qc_stations s
            inner join d2qc_casts c on c.station_id = s.id
            inner join d2qc_depths d on d.cast_id = c.id
            inner join d2qc_data_values dv on dv.depth_id = d.id
            where data_set_id={} and dv.data_type_id={}""".format(
                self.id, parameter_id
            )
        radius = 200000 # radius in meters around points
        buffer = """
            select
            st_buffer(st_union(stat.position)::geography, {})::geometry
            from ({}) stat
        """.format(radius, stations)
        sql = """
            select st_astext(st_union(st.position)) from d2qc_stations st
            where st.data_set_id<>{}  and st_contains(({}), st.position)
        """.format(self.id, buffer)

        cursor = connection.cursor()
        cursor.execute(sql)
        return cursor.fetchall()[0][0]

class DataType(models.Model):
    class Meta:
        db_table = 'd2qc_data_types'
        unique_together = ('original_label', 'identifier', 'data_unit')

    id = models.AutoField(primary_key=True)
    data_unit = models.ForeignKey(
        'DataUnit',
        on_delete = models.CASCADE,
        blank = True,
        null = True,
    )
    identifier = models.CharField(max_length=20, default='', blank=True)
    prefLabel = models.CharField(max_length=255, default='', blank=True)
    altLabel = models.CharField(max_length=255, default='', blank=True)
    definition = models.CharField(max_length=255, default='', blank=True)
    original_label = models.CharField(max_length=20, default='')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    def __str__(self):
        label = self.original_label if self.original_label else self.identifier
        return label

class DataUnit(models.Model):
    class Meta:
        db_table = 'd2qc_data_units'

    id = models.AutoField(primary_key=True)
    identifier = models.CharField(max_length=20, default='', blank=True)
    prefLabel = models.CharField(max_length=255, default='', blank=True)
    altLabel = models.CharField(max_length=255, default='', blank=True)
    definition = models.CharField(max_length=255, default='', blank=True)
    original_label = models.CharField(max_length=20, default='')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    def __str__(self):
        label = self.original_label if self.original_label else self.identifier
        return label

class Station(models.Model):
    class Meta:
        db_table = 'd2qc_stations'
        unique_together = (
                'position',
                'station_number',
                'data_set',
        )
        ordering = ['data_set', 'station_number']

    id = models.AutoField(primary_key=True)
    data_set = models.ForeignKey('DataSet', related_name='stations',
            on_delete=models.CASCADE)
    position = models.PointField(srid=4326, spatial_index=True)
    station_number = models.IntegerField(null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    def __str__(self):
        label = str(self.station_number)
        return label

class Cast(models.Model):
    class Meta:
        db_table = 'd2qc_casts'

    id = models.AutoField(primary_key=True)
    station = models.ForeignKey('Station',
            related_name='casts', on_delete=models.CASCADE)
    cast = models.IntegerField(null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

class Depth(models.Model):
    class Meta:
        db_table = 'd2qc_depths'
        indexes = [
            models.Index(fields=['depth']),
        ]
        unique_together = ( 'cast', 'depth', 'bottle', 'date_and_time')
        ordering = ['depth']

    id = models.AutoField(primary_key=True)
    cast = models.ForeignKey('Cast',
            related_name='depths', on_delete=models.CASCADE)
    depth = models.DecimalField(max_digits=8, decimal_places=3)
    date_and_time = models.DateTimeField()
    bottle = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

class DataValue(models.Model):
    class Meta:
        db_table = 'd2qc_data_values'
        unique_together = ('depth', 'data_type')

    id = models.AutoField(primary_key=True)
    depth = models.ForeignKey('Depth', related_name='data_values',
            on_delete=models.CASCADE)
    data_type = models.ForeignKey('DataType', on_delete=models.CASCADE)
    value = models.DecimalField(max_digits=16, decimal_places=8)
    qc_flag = models.IntegerField(blank=True, null=True)
    qc2_flag = models.IntegerField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    def save(self, *args, **kwargs):
        try:
            v = Decimal(self.value)
        except ValueError:
            logger.error('Data Value ' + self.value + ' is not a float value')
        if not math.isnan(v) and int(v) != -9999:
            super(DataValue, self).save(*args, **kwargs)
