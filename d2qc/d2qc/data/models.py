from django.contrib.gis.db import models
from django.forms import ModelForm
from django.contrib.auth.models import User
from django.conf import settings
from django.core.cache import cache
from django.contrib.gis.geos import Point
import os.path
from django.utils import timezone
import logging
import re
from decimal import Decimal
import math
from django.db import connection
import gsw
import glodap.util.interp as interp
import glodap.util.stats as stats
import glodap.util.geo as geo
import glodap.util.excread as excread
import pandas as pd
import statistics as stat

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
    import_errors = models.TextField(blank=True)
    import_started = models.DateTimeField(null=True)
    import_finnished = models.DateTimeField(null=True)

    # Messages reported while importing data
    _messages = []

    def __str__(self):
        return self.name if self.name else self.filepath

    # Delete files as object is deleted
    def delete(self):
        # Dont delete file if file has related data set(s)
        if not DataSet.objects.filter(data_file_id=self.id).exists():
            self.filepath.delete()
        super().delete()

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
                with open(path, encoding="iso-8859-1") as excfile:
                    filearray = excfile.readlines()
        return filearray

    def _write_messages(self, append = False, save = False):
        if append:
            self.import_errors += '\n'.join(self._messages)
        else:
            self.import_errors = '\n'.join(self._messages)
        if save:
            self.save()

    def import_data(self):
        """
        Import data from this data file. Abort if data existsself. Import errors
        are appended to the import_errors field.

        return True if data was imported, else return False
        """
        if self.import_started:
            self._messages = ["File data already beeing imported"]
            self._write_messages(append = True, save = True)
            return False

        self.import_started = timezone.now()
        self.save()

        datagrid = excread.excread(str(self.filepath))

        MANDATORY_VARS = (
            'EXPOCODE', 'EXC_DATETIME', 'EXC_CTDDEPTH', 'STNNBR', 'LATITUDE',
            'LONGITUDE',
        )

        # Variables not to be treated as data variables
        IGNORE = (
            'EXPOCODE', 'EXC_DATETIME', 'EXC_CTDDEPTH', 'STNNBR', 'SECT_ID', 'DATE',
            'TIME', 'LATITUDE', 'LONGITUDE', 'BTLNBR', 'BTLNBR_FLAG_W',
            'SAMPNO', 'CASTNO', 'CTDDEPTH', 'CTDDEP', 'HOUR', 'MINUTE', 'DEPTH'
        )

        QC_SUFFIX = '_FLAG_W'


        # Check all mandatory variables are there
        depth = ''
        stnnbr = ''
        castno = ''
        data_set = None
        station = None
        cast = None
        depth = None
        # Raise an exception if mandatory columns are missing
        if not all(key in datagrid.columns for key in MANDATORY_VARS):
            message = "Data file missing some mandatory column: {}".format(
                ', '.join(MANDATORY_VARS)
            )
            self._messages.append(message)
            self._write_messages()
            self.import_finnished = timezone.now()
            self.save()
            return False

        # Import data types
        missing_vars = []
        data_types = {str(type_):type_ for type_ in DataType.objects.all()}
        for var in datagrid.columns:
            if var in IGNORE:
                continue
            if var.endswith(QC_SUFFIX):
                continue
            if var not in data_types:
                missing_vars.append(var)

        if missing_vars:
            message = """There where variables in the dataset that are not defined in
            the system. These cannot be handled. An administrator has to add
            the variables as data types for them to be treated. Unhandled
            variables in the data set: {}
            """.format(
                ', '.join(missing_vars)
            )
            self._messages.append(message)

        missing_depth_warning = False # Indicate missing depth already warned
        missing_position_warning = False
        for i, expo in enumerate(datagrid['EXPOCODE']):
            if not data_set or expo != data_set.expocode:
                # Add new dataset
                data_set = DataSet(
                    expocode=expo,
                    is_reference = False,
                    data_file = self,
                    owner = self.owner
                )
                if DataSet.objects.filter(
                            expocode=expo,
                            owner=self.owner
                ).exists():
                    # TODO Support files with multiple datasets, where one or
                    # more might already exist in database, but not all.
                    message = 'Dataset {} already exists for this user'. format(
                        expo
                    )
                    self._messages.append(message)
                    self._write_messages()
                    self.import_finnished = timezone.now()
                    self.save()
                    return False

                data_set.save()
                station = None
                cast = None
                depth = None
            if not station or datagrid['STNNBR'][i] != station.station_number:
                longitude = datagrid['LONGITUDE'][i]
                latitude = datagrid['LATITUDE'][i]
                if math.isnan(longitude) or math.isnan(latitude):
                    if missing_position_warning:
                        continue
                    # Warning and dont insert if depth is NaN
                    message = """Latitude or longitude is nan on line {}.
                    Station will not be added when position is missing.
                    Subsequent missing position errors are supressed for this
                    file.
                    """.format(i)
                    self._messages.append(message)
                    missing_position_warning = True
                    continue
                # Add new station
                station = Station(
                        data_set = data_set,
                        position = Point(longitude, latitude),
                        station_number = datagrid['STNNBR'][i]
                )
                station.save()
                cast = None
                depth = None
            if (
                    not cast or
                    ('CASTNO' in datagrid and datagrid['CASTNO'][i] != cast.cast)
            ):
                # Add new cast
                cast_ = 1
                if 'CASTNO' in datagrid:
                    cast_ = datagrid['CASTNO'][i]
                cast = Cast(
                        station = station,
                        cast = cast_
                )
                cast.save()
                depth = None

            if (
                    not depth
                    or depth.depth != datagrid['EXC_CTDDEPTH'][i]
                    or (
                        'BTLNBR' in datagrid
                        and depth.bottle != datagrid['BTLNBR'][i]
                    )
            ):
                if math.isnan(datagrid['EXC_CTDDEPTH'][i]):
                    if missing_depth_warning:
                        continue
                    # Warning and dont insert if depth is NaN
                    message = """Depth is nan on line {}. Data will not be added when
                            depth is nan. Subsequent missing depth errors are
                            supressed for this file.
                            """.format(i)
                    self._messages.append(message)
                    missing_depth_warning = True
                    continue

                # Add new depth
                btlnbr = datagrid.get('BTLNBR', False)
                depth = Depth(
                        cast = cast,
                        depth = datagrid['EXC_CTDDEPTH'][i],
                        bottle = 1 if btlnbr is False else btlnbr[i],
                        date_and_time = datagrid['EXC_DATETIME'][i],
                )
                depth.save()
            for key in datagrid.columns:
                if key in IGNORE:
                    continue
                if not key in data_types:
                    # Variable not found in database
                    continue
                qc_flag = None
                if key + QC_SUFFIX in datagrid:
                    qc_flag = int(datagrid[key + QC_SUFFIX][i])
                value = DataValue(
                        depth = depth,
                        value = datagrid[key][i],
                        qc_flag = qc_flag,
                        data_type = data_types[key]
                )
                value.save()
        self._write_messages()
        self.import_finnished = timezone.now()
        self.save()
        return True

class DataSet(models.Model):
    class Meta:
        db_table = 'd2qc_data_sets'
        ordering = ['expocode']
        unique_together = ('expocode', 'owner')
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

    def get_data_types(self, min_depth=0):
        """Fetch all data types in this data set from the database"""
        cache_key = "get_data_types-{}".format(self.id)
        value = cache.get(cache_key, False)
        if value is not False:
            return value

        sql = """select distinct dt.original_label, dt.identifier, dt.id
            from d2qc_data_types dt
            inner join d2qc_data_values dv on dv.data_type_id = dt.id
            inner join d2qc_depths d on d.id=dv.depth_id
            inner join d2qc_casts c on c.id=d.cast_id
            inner join d2qc_stations s on c.station_id=s.id
            where s.data_set_id = {}
            and d.depth >= {}
            order by dt.original_label;""".format(
                self.id,
                min_depth
            )

        typelist = [{
            'original_label': type[0],
            'identifier': type[1],
            'id': type[2],
        } for type in self._fetchall_query(sql)]
        # Set the cache
        cache.set(cache_key, typelist)

        return typelist

    def get_stations(
            self,
            parameter_id=None,
            data_set_id=None,
            crossover_radius=False,
            min_depth=False,
    ):
        """
        Get the list of stations in data_set_id or the current data set,
        possibly filtered by parameter_id
        """
        crossover_radius = (
            crossover_radius
            or self.owner.profile.crossover_radius
            or self.crossover_radius
        )
        min_depth = (
            min_depth
            or self.owner.profile.min_depth
            or self.min_depth
        )
        sql = """
            select distinct st.id from d2qc_stations st
            inner join d2qc_data_sets ds on (st.data_set_id = ds.id)
            inner join d2qc_casts c on (c.station_id = st.id)
            inner join d2qc_depths d on (d.cast_id = c.id)
            inner join d2qc_data_values dv on (dv.depth_id = d.id)
            where ds.id = {} and d.depth >= {}
        """.format(
                data_set_id or self.id,
                min_depth
        )

        if parameter_id is not None:
            data_type_clause = """
            and dv.data_type_id in ({})
            """.format(
                self._in_datatype(parameter_id)
            )

            sql = sql + data_type_clause

        return [ row[0] for row in self._fetchall_query(sql) ]

    def get_station_positions(
            self,
            stations: list=[],
    ):
        """
        Get the stations in data_set_id, possibly filtered by parameter_id
        and crossover data set id.

        Returns data as Well Known Text multipoint
        """
        result = None
        sql = """
            select st_astext(st_collect(position))
            from d2qc_stations where id in ({})
        """.format(DataSet._in_stations(stations))
        result = self._fetchall_query(sql, True)[0]
        return result

    @staticmethod
    def _in_stations(stations: list=None):
        """
        Get a commaseparated list of stations suitable for an in() - statment
        in SQL. if the stations - list is empty or none, '-1' is returned.

        eg.
        >>> DataSet._in_stations([4,6,8])
        '4,6,8'
        """
        return ','.join(str(i) for i in stations or ['-1'])

    def _get_stations_buffer(
        self,
        stations: list=[],
        crossover_radius=False,
    ):
        crossover_radius = (
            crossover_radius
            or self.owner.profile.crossover_radius
            or self.crossover_radius
        )
        """
        Get the search buffer for a set of stations
        """
        result = None
        sql = """
            select coalesce(
                st_buffer(st_collect(position)::geography, {})::geometry,
                ST_GeomFromText('POLYGON EMPTY')
            )
            from d2qc_stations where id in ({})
        """.format(
                crossover_radius,
                DataSet._in_stations(stations),
        )

        result = self._fetchall_query(sql, True)[0]

        return result

    def get_stations_polygon(
            self,
            stations: list,
            crossover_radius=False,
        ):
        """
        Get the polygon around stations that define the serach area for
        matching crossover stations.

        Returns the polygon as Well Known Text multipolygon.
        """
        if len(stations) == 0:
            return []
        crossover_radius = (
            crossover_radius
            or self.owner.profile.crossover_radius
            or self.crossover_radius
        )
        result = None
        sql = """
            select st_astext('{}')
        """.format(self._get_stations_buffer(
            stations,
            crossover_radius=crossover_radius,
        ))
        result = self._fetchall_query(sql, True)[0]

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
            self._single_data_type_ids[parameter_id] = self._fetchall_query(
                sql,
                True,
            )[0]

        return self._single_data_type_ids[parameter_id]

    def get_crossover_stations(
            self,
            data_set_id=None,
            stations: list=None,
            parameter_id=None,
            crossover_data_set_id=None,
            min_depth=False,
            crossover_radius=False,
        ):
        """
        Get stations that are within the crossover range of stations in this
        data set (default 200km), for the given parameter. If data_set_id
        is given, only get stations in the given data set.
        """

        min_depth = (
            min_depth
            or self.owner.profile.min_depth
            or self.min_depth
        )
        crossover_radius = (
            crossover_radius
            or self.owner.profile.crossover_radius
            or self.crossover_radius
        )
        select = """
            select distinct st.id
        """
        _from = """
            from d2qc_stations st
            inner join d2qc_data_sets ds on (st.data_set_id = ds.id)
            inner join d2qc_casts c on (c.station_id = st.id)
            inner join d2qc_depths d on (d.cast_id = c.id)
        """
        where = """
            where ds.id <> {} and d.depth >= {}
        """.format(
                data_set_id or self.id,
                min_depth
        )

        if parameter_id is not None:
            _from += """
                inner join d2qc_data_values dv on (dv.depth_id = d.id)
            """
            where += """
                and dv.data_type_id in ({})
            """.format(
                    self._in_datatype(parameter_id)
            )

        if stations is not None:
            where += """
                and st_contains('{}', st.position)
            """.format(
                self._get_stations_buffer(
                    stations,
                    crossover_radius=crossover_radius,
                )
            )

        if crossover_data_set_id is not None:
            where += """
                and ds.id = {}
            """.format(
                    crossover_data_set_id
            )

        sql = select + _from + where

        return [row[0] for row in self._fetchall_query(sql)]

    def get_station_data_sets(
        self,
        stations: list,
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
                DataSet._in_stations(stations)
            )
            result = self._fetchall_query(sql)

        return result

    def _fetchall_query(self, sql, only_one=False):
        """
        Executes an sql query, returning the resulting data.
        """
        cache_key = "_fetchall_query-{}".format(hash(sql))
        query = cache.get(cache_key, False)
        if not query:
            cursor = connection.cursor()
            cursor.execute(sql)
            if only_one:
                query = cursor.fetchone()
            else:
                query = cursor.fetchall()
            cache.set(cache_key, query)
        return query

    def get_profiles_data(
            self,
            stations: list,
            parameter_id,
            crossover_radius=False,
            min_depth=False,
    ):
        """
        Get profiles for the stations and the given parameter_id.

        Returns a pandas dataframe
        """
        crossover_radius = (
            crossover_radius
            or self.owner.profile.crossover_radius
            or self.crossover_radius
        )
        min_depth = (
            min_depth
            or self.owner.profile.min_depth
            or self.min_depth
        )
        cache_key = "get_profiles_data-{}-{}-{}-{}-{}".format(
            self.id,
            parameter_id,
            hash(tuple(stations)),
            crossover_radius,
            min_depth,
        )
        value = cache.get(cache_key, False)
        if value is not False:
            return value

        columns = [
            'data_set_id',
            'expocode',
            'station_number',
            'cast',
            'depth',
            'param',
            'temp',
            'salin',
            'press',
            'longitude',
            'latitude',
        ]
        sql_tmpl = """
            select distinct on(d.id) data_set_id, ds.expocode, s.station_number, c.cast as c_cast,
            d.depth::float as depth, dv.value::float as param,
            temp.value::float as temp, salt.value::float as salin,
            pres.value::float as press,
            st_x(s.position) as longitude, st_y(s.position)  as latitude
            from d2qc_depths d
            left join d2qc_data_values dv on (
                dv.depth_id = d.id and dv.data_type_id in ({})
            )
            left join d2qc_data_values temp on (
                temp.depth_id = d.id
            )
            left join d2qc_data_values salt on (
                salt.depth_id = d.id
            )
            left join d2qc_data_values pres on (
                pres.depth_id = d.id
            )
            inner join d2qc_casts c on (d.cast_id = c.id)
            inner join d2qc_stations s on (c.station_id = s.id)
            inner join d2qc_data_sets ds on (s.data_set_id = ds.id)
            where
            temp.data_type_id in (39, 65) AND
            salt.data_type_id in (8, 33) AND
            pres.data_type_id in (77, 45) AND
            s.id in({}) and depth>={}
        """

        sql = sql_tmpl.format(
            self._in_datatype(parameter_id),
            DataSet._in_stations(stations),
            min_depth,
        )

        sql += " order by d.id, expocode, station_number, c_cast, depth"
        _all = self._fetchall_query(sql)
        dataframe = pd.DataFrame(_all, columns=columns)
        # Use GSW to calculate sigma4
        dataframe['sigma4'] = gsw.density.sigma4(
            gsw.conversions.SA_from_SP(
                dataframe['salin'],
                dataframe['press'],
                dataframe['longitude'],
                dataframe['latitude'],
            ),
            dataframe['temp'],
        )
        cache.set(cache_key, dataframe)

        return dataframe

    def get_profiles_as_json(
            self,
            dataframe,
            independent_var='sigma4',
    ):
        """
        Takes a DataFrame as generated by get_profiles_data and
        get_interp_profiles, and return a JSON array of structs:
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

        groups = dataframe.groupby(
            [
                'data_set_id',
                'expocode',
                'station_number'
            ]
        )
        profiles = []
        for groupval, df in groups:
            if df.size == 0:
                continue
            profile = []
            profile.append('"{}":{}'.format(
                independent_var,
                df[independent_var].to_json(
                    orient='split',
                    index=False,
                )
            ))
            profile.append('"{}":{}'.format(
                'param',
                df['param'].to_json(
                    orient='split',
                    index=False,
                )
            ))
            profile.append('"{}":"{}"'.format(
                'expocode',
                df.iloc[0]['expocode']
            ))
            profile.append('"{}":"{}"'.format(
                'data_set_id',
                df.iloc[0]['data_set_id']
            ))

            profile.append('"{}":"{}"'.format(
                'station_number',
                df.iloc[0]['station_number']
            ))
            profile = "{" + ",".join(profile) + "}"

            profiles.append(profile)
        profiles = "[" + ",".join(profiles) + "]"

        return profiles

    def get_timespan(self, stations: list=[]):
        """
        Get the first and last data timestamp for this cruise
        Optionally provide a list of stations to filter the result.

        stations: list of station id's, ignoring id's not from this cruise

        retuns a tuple with two date objects (start, end)
        """

        sql = """
            SELECT min(date_and_time), max(date_and_time) FROM d2qc_depths d
            INNER JOIN d2qc_casts c on d.cast_id = c.id
            INNER JOIN d2qc_stations s on c.station_id = s.id
            WHERE s.data_set_id = {}
        """.format(self.id)
        if len(stations) > 0:
            sql += """
            AND s.id in ({})
            """.format(self._in_stations(stations))
        return self._fetchall_query(sql)[0]

    def get_interp_profiles(
            self,
            stations,
            parameter_id,
            crossover_radius=False,
            min_depth=False,
    ):
        """
        Fetches profiles for the given stations, and interpolates these
        to a common depth/sigma4 parameter to allow comparing profiles with
        different depths initially. Returns a dataframe with same format as
        get_profiles_data
        """
        crossover_radius = (
            crossover_radius
            or self.owner.profile.crossover_radius
            or self.crossover_radius
        )
        min_depth = (
            min_depth
            or self.owner.profile.min_depth
            or self.min_depth
        )
        cache_key = "get_interp_profiles-{}-{}-{}-{}-{}".format(
            self.id,
            parameter_id,
            hash(tuple(stations)),
            crossover_radius,
            min_depth,
        )
        value = cache.get(cache_key, False)
        if value is not False:
            return value

        dataframe = self.get_profiles_data(
            stations,
            parameter_id,
            crossover_radius=crossover_radius,
            min_depth=min_depth,
        )
        groups = dataframe.groupby(
            [
                'data_set_id',
                'station_number'
            ]
        )
        profiles = []
        suffix = '_interp'
        xtype = 'sigma4'

        # Generate sigma4 sequence according to xover_2ndQC.m
        if xtype == 'sigma4':
            xtype_interp = interp.generate_regular_monotonus_squence(
                _min=44,
                _max=45.7,
                step=.01,
            )
            xtype_interp += interp.generate_regular_monotonus_squence(
                _min=45.701,
                _max=45.88,
                step=.0025,
            )
            xtype_interp += interp.generate_regular_monotonus_squence(
                _min=45.881,
                _max=46.5,
                step=.001,
            )
        elif xtype == 'depth':
            xtype_interp = interp.generate_regular_monotonus_series(
                _min=dataframe['depth'].min(),
                _max=dataframe['depth'].max(),
                step = 20
            )
        columns = [
            'data_set_id',
            'station_number',
            'expocode',
            xtype,
            'param',
            'latitude',
            'longitude',
        ]
        for groupval, data in groups:
            try:
                if 'expocode' in data:
                    expocode = data['expocode'].iloc[0]
                data = interp.remove_nans(data, ['depth', 'param', 'sigma4'])
                data = interp.sort_data_set_on_dimension(data, xtype)
                data = interp.average_values_for_duplicate_dimension(data, xtype)
                x = data[xtype].tolist()
                y = data['param'].tolist()
                # xover on density surface (se xover_2ndQC.m line 99)
                x_interp,param_interp=interp.pchip_interpolate_profile(
                    x=x,
                    y=y,
                    x_interp=xtype_interp,
                )
                # sigma4 gaps calculated from depth gaps defined in intprofile.m
                # 300m gap between 500m depth =>
                x_interp,param_interp = interp.subst_depth_profile_gaps_with_nans(
                    x_interp,
                    param_interp,
                    data['depth'].tolist(),
                    x,
                )
                dataframe = pd.DataFrame(columns=columns)

                dataframe[xtype] = x_interp
                dataframe['param'] = param_interp
                dataframe=dataframe.iloc[
                    dataframe.param.first_valid_index():dataframe.param.last_valid_index()
                ]

                for c in dataframe.columns:
                    if c in ['param', xtype, 'depth']:
                        continue
                    elif c == 'expocode':
                        dataframe[c] = expocode
                    else:
                        dataframe[c] = data[c].iloc[0]

                # Trim nan-rows at start and end
                first = dataframe['param'].first_valid_index()
                last = dataframe['param'].last_valid_index()
                dataframe = dataframe.loc[first:last, :]

                profiles.append(dataframe)
            except Exception as e:
                print("#################### WARNING #####################")
                print(e)
                dataframe = None
        if len(profiles)>1:
            profiles = pd.concat(profiles, sort=False)
        elif len(profiles)==1:
            profiles=profiles[0]
        else:
            profiles = pd.DataFrame(columns=columns)
        cache.set(cache_key, profiles)
        return profiles


    def get_profiles_stats(
            self,
            stations: list,
            xover_stations: list,
            parameter_id: int,
            crossover_radius=False,
            min_depth=False,
    ):
        crossover_radius = (
            crossover_radius
            or self.owner.profile.crossover_radius
            or self.crossover_radius
        )
        min_depth = (
            min_depth
            or self.owner.profile.min_depth
            or self.min_depth
        )
        data_type = DataType.objects.get(pk=parameter_id)
        cache_key = "get_profiles_stats-{}-{}-{}-{}-{}-{}".format(
            self.id,
            parameter_id,
            hash(tuple(stations)),
            crossover_radius,
            min_depth,
            data_type.offset_type.id,
        )
        value = cache.get(cache_key, False)
        if value is not False:
            return value

        current_stations = self.get_interp_profiles(
            stations,
            parameter_id,
            crossover_radius=crossover_radius,
            min_depth=min_depth,
        )
        reference_stations = self.get_interp_profiles(
            xover_stations,
            parameter_id,
            crossover_radius=crossover_radius,
            min_depth=min_depth,
        )
        if reference_stations.size == 0 or current_stations.size == 0:
            cache.set(cache_key, {})
            return {}

        current_stations = current_stations.groupby(
            [
                'station_number'
            ]
        )
        xtype = 'sigma4'
        ref_expocode = reference_stations.expocode.iloc[0]
        ref_data_set_id = reference_stations.data_set_id.iloc[0]
        reference_stations = reference_stations.groupby(
            [
                'data_set_id',
                'station_number'
            ]
        )


        profiles = []
        diffs = {}
        for groupval, current in current_stations:
            for g2, reference in reference_stations:
                if (
                        geo.haversine_distance(
                            current['longitude'].iloc[0],
                            current['latitude'].iloc[0],
                            reference['longitude'].iloc[0],
                            reference['latitude'].iloc[0],
                        ) < crossover_radius
                ):
                    c_ind, r_ind = stats._get_matching_indices(
                        current.sigma4.tolist(),
                        reference.sigma4.tolist(),
                    )
                    param = current.columns.get_loc('param')
                    sigma4 = current.columns.get_loc(xtype)
                    c_param = current.iloc[c_ind, param].tolist()
                    r_param = reference.iloc[r_ind, param].tolist()
                    y_all = reference.iloc[r_ind, sigma4].tolist()
                    for i, y in enumerate(y_all):
                        if not y in diffs:
                            diffs[y] = {'diff': []}
                        if data_type.offset_type.id == 1:
                            val = c_param[i] - r_param[i]
                            if val is None or math.isnan(val):
                                continue
                            diffs[y]['diff'].append(val)
                        elif data_type.offset_type.id == 2:
                            val = c_param[i] / r_param[i]
                            if val is None or math.isnan(val):
                                continue
                            diffs[y]['diff'].append(val)
        has_std = False
        for y in diffs:
            if len(diffs[y]['diff']) > 0:
                diffs[y]['mean'] = stat.mean(diffs[y]['diff'])
                diffs[y]['stdev'] = None
                if len(diffs[y]['diff']) > 4:
                    diffs[y]['stdev'] = stat.stdev(diffs[y]['diff'])
                    has_std = True
            diffs[y].pop('diff')

        mean = []
        stdev = []
        y=[]
        w_mean = None
        w_stdev = None
        result = None
        for key, value in diffs.items():
            if not 'mean' in value:
                continue
            y.append(key)
            mean.append(value['mean'])
            stdev.append(value['stdev'])
        if len(mean) > 0:
            # Sort the lists by y-value
            zipped = sorted(zip(y, mean, stdev))
            # ...and unzip
            y, mean, stdev = zip(*zipped)

            ###############################################################
            # TODO If std less than minimum std, set std to minimum - std #
            # see line 73 xover_2ndQC.m                                   #
            ###############################################################

            # Calculate weighted difference
            if has_std:
                w_mean = sum([ 0 if not s else m/pow(s, 2) for m, s in zip(mean, stdev)])
                w_mean = w_mean / sum([ 0 if not s else 1/pow(s, 2) for s in stdev])
                w_stdev = sum([ 0 if not s else 1/s for s in stdev])
                w_stdev = w_stdev / sum([ 0 if not s else 1/pow(s, 2) for s in stdev])

            result = {
                'y': y,
                'mean': mean,
                'stdev': stdev,
                'w_mean': w_mean,
                'w_stdev': w_stdev,
                'expocode': ref_expocode,
                'data_set_id': int(ref_data_set_id),
            }
            cache.set(cache_key, result)

        return result


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
    offset_type = models.ForeignKey(
        'OffsetType',
        on_delete = models.PROTECT,
        blank = True,
        null = True,
        default = 1,
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    def __str__(self):
        label = self.original_label if self.original_label else self.identifier
        return label

class OffsetType(models.Model):
    class Meta:
        db_table = 'd2qc_offset_types'
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20, default='', blank=True)
    description = models.CharField(max_length=255, default='', blank=True)
    def __str__(self):
        return self.name

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
