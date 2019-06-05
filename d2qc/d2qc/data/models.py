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
import hashlib

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
    _single_data_type_ids = {}
    _stations = {}
    _contains_polygon = {}
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

    def get_stations(
            self,
            parameter_id=None,
            data_set_id=None
    ):
        """
        Get the list of stations in the current data set,
        possibly filtered by parameter_id
        """
        sql = """
            select string_agg(distinct st.id::text, ',') from d2qc_stations st
            inner join d2qc_data_sets ds on (st.data_set_id = ds.id)
            inner join d2qc_casts c on (c.station_id = st.id)
            inner join d2qc_depths d on (d.cast_id = c.id)
            inner join d2qc_data_values dv on (dv.depth_id = d.id)
            where ds.id = {} and d.depth >= {}
        """.format(
                data_set_id or self.id,
                self.owner.profile.min_depth
        )

        if parameter_id is not None:
            data_type_clause = """
            and dv.data_type_id in ({})
            """.format(
                self._in_datatype(parameter_id)
            )

            sql = sql + data_type_clause

        cursor = connection.cursor()
        cursor.execute(sql)
        return cursor.fetchall()[0][0]


    def get_station_positions(
            self,
            stations
    ):
        """
        Get the stations in data_set_id, possibly filtered by parameter_id
        and crossover data set id.

        Returns data as Well Known Text multipoint
        """
        result = None
        if stations is not None:
            sql = """
                select st_astext(st_collect(position))
                from d2qc_stations where id in ({})
            """.format(stations)

            cursor = connection.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()[0][0]
        return result

    def _get_stations_buffer(
        self,
        stations
    ):
        """
        Get the search buffer for a set of stations
        """
        result = None
        if stations is not None:
            sql = """
                select st_buffer(st_collect(position)::geography, {})::geometry
                from d2qc_stations where id in ({})
            """.format(
                    self.owner.profile.crossover_radius,
                    stations
            )

            cursor = connection.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()[0][0]

        return result

    def get_stations_polygon(
            self,
            stations
    ):
        """
        Get the polygon around stations that define the serach area for
        matching crossover stations.

        Returns the polygon as Well Known Text multipolygon.
        """
        result = None
        if stations is not None:
            sql = """
                select st_astext('{}')
            """.format(self._get_stations_buffer(stations))
            cursor = connection.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()[0][0]

        return result

    def _in_datatype(self, parameter_id):
        """
        Get datatypes that has the same bodc id as the given parameter_id.

        Returns a commaseparated list of data_set_id's
        """
        if parameter_id not in self._single_data_type_ids:
            sql = """
                select string_agg(dt2.id::text, ',') from d2qc_data_types dt
                inner join d2qc_data_types dt2 on dt.identifier=dt2.identifier
                where dt.id={}  OFFSET 0
            """.format(parameter_id)
            cursor = connection.cursor()
            cursor.execute(sql)
            self._single_data_type_ids[parameter_id] = cursor.fetchone()[0]

        return self._single_data_type_ids[parameter_id]

    def get_crossover_stations(
            self,
            data_set_id=None,
            stations=None,
            parameter_id=None,
            crossover_data_set_id=None,
    ):
        """
        Get stations that are within the crossover range of stations in this
        data set (default 200km), for the given parameter. If data_set_id
        is given, only get stations in the given data set.
        """
        sql = """
            select string_agg(distinct st.id::text, ',') from d2qc_stations st
            inner join d2qc_data_sets ds on (st.data_set_id = ds.id)
            inner join d2qc_casts c on (c.station_id = st.id)
            inner join d2qc_depths d on (d.cast_id = c.id)
            inner join d2qc_data_values dv on (dv.depth_id = d.id)
            where ds.id <> {} and d.depth >= {}
        """.format(
                data_set_id,
                self.owner.profile.min_depth
        )

        if parameter_id is not None:
            data_type_clause = """
                and dv.data_type_id in ({})
            """.format(
                    self._in_datatype(parameter_id)
            )

            sql = sql + data_type_clause

        if stations is not None:
            buffer_clause = """
                and st_contains('{}', st.position)
            """.format(
                self._get_stations_buffer(stations)
            )

            sql = sql + buffer_clause

        if crossover_data_set_id is not None:
            dataset_clause = """
                and ds.id = {}
            """.format(
                    crossover_data_set_id
            )

            sql = sql + dataset_clause


        cursor = connection.cursor()
        cursor.execute(sql)
        return cursor.fetchall()[0][0]

    def get_station_data_sets(
        self,
        stations
    ):
        """
        Get the data set details for a set of stations

        Returns a list:
            [[data-set_id, expocode, station_count, time_first_station], ...]
        """
        result = None
        if stations is not None:
            sql = """
                select ds.id, ds.expocode,
                count(distinct st.id) as station_count,
                min(d.date_and_time) as first_station
                from d2qc_stations st
                inner join d2qc_data_sets ds on (st.data_set_id = ds.id)
                inner join d2qc_casts c on (c.station_id = st.id)
                inner join d2qc_depths d on (d.cast_id = c.id)
                where st.id in ({})
                group by ds.id
                order by first_station
            """.format(
                stations
            )

            cursor = connection.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()

        return result

    def get_profiles(self, stations, parameter_id):
        """
        Get profiles for the specified stations

        Returns an array of structs:
        [
            {
                data_set_id:...,
                expocode:...,
                station_number:...,
                cast:...,
                depth:[...],
                value:[...],
            }
        ]
        """

        sql = """
            select ds.id, ds.expocode, s.station_number, c.cast as c_cast,
            d.depth::float, dv.value::float
            from d2qc_data_values dv
            inner join d2qc_depths d on (dv.depth_id = d.id)
            inner join d2qc_casts c on (d.cast_id = c.id)
            inner join d2qc_stations s on (c.station_id = s.id)
            inner join d2qc_data_sets ds on (s.data_set_id = ds.id)
            where dv.data_type_id in ({}) and s.id in({}) and depth>={}
        """.format(
                self._in_datatype(parameter_id),
                stations,
                self.owner.profile.min_depth
        )

        sql += " order by expocode, station_number, c_cast, depth"
        cursor = connection.cursor()
        cursor.execute(sql)
        profiles = []
        data_set = None
        station = None
        cast = None
        current = {}
        for row in cursor.fetchall():
            if (
                    row[0] != data_set
                    or row[2] != station
                    or row[3] != cast
            ):
                if current:
                    profiles.append(current)
                current = {
                    'data_set_id': row[0],
                    'expocode': row[1],
                    'station_number': row[2],
                    'cast': row[3],
                    'depth': [],
                    'value': [],
                }
                data_set = current['data_set_id']
                station = current['station_number']
                cast = current['cast']
            current['depth'].append(row[4])
            current['value'].append(row[5])
        if current:
            profiles.append(current)

        return profiles


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
