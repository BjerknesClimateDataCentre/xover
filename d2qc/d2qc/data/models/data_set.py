import math
import gsw
import pandas as pd
import statistics as stat

from django.contrib.gis.db import models
from django.contrib.auth.models import User
from django.db import connection
from django.core.cache import cache

import glodap.util.interp as interp
import glodap.util.stats as stats
import glodap.util.geo as geo

import d2qc.data as data

class DataSet(models.Model):
    class Meta:
        db_table = 'd2qc_data_sets'
        ordering = ['expocode']
        unique_together = ('expocode', 'owner')
    _single_data_type_name_ids = {}
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
    temp_aut = models.ForeignKey(
        'DataTypeName',
        on_delete = models.PROTECT,
        null=True,
        related_name='temp_aut',
    )
    press_aut = models.ForeignKey(
        'DataTypeName',
        on_delete = models.PROTECT,
        null=True,
        related_name='press_aut',
    )
    salin_aut = models.ForeignKey(
        'DataTypeName',
        on_delete = models.PROTECT,
        null=True,
        related_name='salin_aut',
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    _typelist = None

    def __str__(self):
        return self.expocode

    def set_type_list(self, typelist):
        """Reset list of types for this data set"""
        self._typelist = typelist

    def get_data_types(self, min_depth=0):
        """Fetch all data types in this data set from the database"""

        if self._typelist:
            return self._typelist

        sql = """select distinct dtn.name, dt.identifier, dtn.id
            from d2qc_data_type_names dtn
            inner join d2qc_data_types dt on dtn.data_type_id=dt.id
            inner join d2qc_data_values dv on dv.data_type_name_id = dtn.id
            inner join d2qc_depths d on d.id=dv.depth_id
            inner join d2qc_casts c on c.id=d.cast_id
            inner join d2qc_stations s on c.station_id=s.id
            where s.data_set_id = {}
            and d.depth >= {}
            order by dtn.name;""".format(
                self.id,
                min_depth
            )

        typelist = [{
            'original_label': type[0],
            'identifier': type[1],
            'id': type[2],
        } for type in DataSet._fetchall_query(sql)]
        # Set the cache
        self._typelist = typelist
        return typelist

    def get_stations(
            self,
            parameter_id = None,
            data_set_id = None,
            crossover_radius = 200000,
            min_depth = 0,
    ):
        """
        Get the list of stations in data_set_id or the current data set,
        possibly filtered by parameter_id
        """

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
            sql += """
                and dv.data_type_name_id = {}
            """.format(parameter_id)

        return [ row[0] for row in DataSet._fetchall_query(sql) ]

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
        result = DataSet._fetchall_query(sql, True)[0]
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
        crossover_radius=200000,
    ):

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

        result = DataSet._fetchall_query(sql, True)[0]

        return result

    def get_stations_polygon(
            self,
            stations: list,
            crossover_radius=200000,
        ):
        """
        Get the polygon around stations that define the serach area for
        matching crossover stations.

        Returns the polygon as Well Known Text multipolygon.
        """
        if len(stations) == 0:
            return []

        result = None
        sql = """
            select st_astext('{}')
        """.format(self._get_stations_buffer(
            stations,
            crossover_radius=crossover_radius,
        ))
        result = DataSet._fetchall_query(sql, True)[0]

        return result

    def _in_datatype(self, parameter_id):
        """
        Get datatypes that has the same bodc id as the given parameter_id.

        Returns a commaseparated list of data_set_id's
        """
        if parameter_id not in self._single_data_type_name_ids:
            sql = """
                select string_agg(distinct dtn2.id::text, ',')
                from d2qc_data_type_names dtn
                inner join d2qc_data_types dt on dtn.data_type_id=dt.id
                inner join d2qc_data_type_names dtn2 on dtn2.data_type_id=dt.id
                where dtn.id={}  OFFSET 0
            """.format(parameter_id)
            self._single_data_type_name_ids[parameter_id] = DataSet._fetchall_query(
                sql,
                True,
            )[0]

        return self._single_data_type_name_ids[parameter_id]

    def get_crossover_stations(
            self,
            data_set_id = None,
            stations: list = None,
            parameter_id = None,
            crossover_data_set_id = None,
            min_depth = 0,
            crossover_radius = 200000,
            minimum_num_stations = 1,
        ):
        """
        Get stations that are within the crossover range of stations in this
        data set (default 200km), for the given parameter. If data_set_id
        is given, only get stations in the given data set. If
        minimum_num_stations > 1, only return stations where there is at least
        minimum_num_stations in the data set (for the given parameter_id).
        """

        select = """
            select string_agg(distinct st.id::text, ',')
        """
        _from = """
            from d2qc_stations st
            inner join d2qc_data_sets ds on (st.data_set_id = ds.id)
            inner join d2qc_casts c on (c.station_id = st.id)
            inner join d2qc_depths d on (d.cast_id = c.id)
        """
        where = """
            where d.depth >= {}
        """.format(
                min_depth,
        )
        group_by = """
            GROUP BY st.data_set_id
        """
        having = ""
        if minimum_num_stations > 1:
            having = """
                HAVING count(distinct st.id) >= {}
            """.format(minimum_num_stations)

        if parameter_id is not None:
            _from += """
                inner join d2qc_data_values dv on (dv.depth_id = d.id)
            """
            where += """
                and dv.data_type_name_id in ({})
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
        else:
            where += """
                and ds.id <> {}
            """.format(
                data_set_id or self.id,
            )

        sql = select + _from + where + group_by + having

        # Get a list with stations for each data set as a commaseparated list
        stations_string_list = [row[0] for row in DataSet._fetchall_query(sql)]
        if stations_string_list and stations_string_list[0]:
            # ...and return a normal list with the stations
            return ','.join(stations_string_list).split(',')
        else:
            return []

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
            result = DataSet._fetchall_query(sql)

        return result

    @staticmethod
    def _fetchall_query(sql, only_one=False):
        """
        Executes an sql query, returning the resulting data.
        """
        cursor = connection.cursor()
        cursor.execute(sql)
        if only_one:
            query = cursor.fetchone()
        else:
            query = cursor.fetchall()
        return query

    def get_profiles_data(
            self,
            stations: list,
            parameter_id,
            min_depth = 0,
            only_this_parameter = False,
    ):
        """
        Get profiles for the stations and the given parameter_id.

        Returns a pandas dataframe
        """

        cache_key = "get_profiles_data-{}-{}-{}-{}".format(
            self.id,
            parameter_id,
            hash(tuple(stations)),
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
            'depth_id',
        ]

        sql_tmpl = """
            select distinct on(d.id) data_set_id, ds.expocode, s.station_number,
            c.cast as c_cast, d.depth::float as depth, dv.value::float as param,
            temp.value::float as temp, salt.value::float as salin,
            pres.value::float as press,
            st_x(s.position) as longitude, st_y(s.position)  as latitude,
            d.id as depth_id
            from d2qc_depths d
            left join d2qc_data_values dv on (
                dv.depth_id = d.id and dv.data_type_name_id in ({})
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
            temp.data_type_name_id = ds.temp_aut_id AND
            salt.data_type_name_id = ds.salin_aut_id AND
            pres.data_type_name_id = ds.press_aut_id AND
            dv.qc_flag in (2,6) AND
            s.id in({}) and depth>={}
        """
        parameters = parameter_id
        if not only_this_parameter:
            parameters = self._in_datatype(parameter_id)
        sql = sql_tmpl.format(
            parameters,
            DataSet._in_stations(stations),
            min_depth,
        )

        sql += " order by d.id"

        # wrap query as a sub-query to allow correct ordering
        sql = """
            select data.* from ({}) data
            order by expocode, station_number, c_cast, depth
        """.format(sql)

        _all = DataSet._fetchall_query(sql)
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

    @staticmethod
    def get_reference_parameter(identifier):
        sql = """
            select dtn.id
            from d2qc_data_types dt
            inner join d2qc_data_type_names dtn on dt.id=dtn.data_type_id
            where dtn.is_reference and dt.identifier = '{}'
            limit 1
        """.format(identifier)
        return DataSet._fetchall_query(sql)[0][0]

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
        return DataSet._fetchall_query(sql)[0]

    def get_interp_profiles(
            self,
            stations,
            parameter_id,
            min_depth=0,
    ):
        """
        Fetches profiles for the given stations, and interpolates these
        to a common depth/sigma4 parameter to allow comparing profiles with
        different depths initially. Returns a dataframe with same format as
        get_profiles_data
        """

        cache_key = "get_interp_profiles-{}-{}-{}-{}".format(
            self.id,
            parameter_id,
            hash(tuple(stations)),
            min_depth,
        )
        value = cache.get(cache_key, False)
        if value is not False:
            return value

        dataframe = self.get_profiles_data(
            stations,
            parameter_id,
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
        for groupval, _data in groups:
            try:
                if 'expocode' in _data:
                    expocode = _data['expocode'].iloc[0]
                _data = interp.remove_nans(_data, ['depth', 'param', 'sigma4'])
                _data = interp.sort_data_set_on_dimension(_data, xtype)
                _data = interp.average_values_for_duplicate_dimension(_data, xtype)
                x = _data[xtype].tolist()
                y = _data['param'].tolist()
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
                    _data['depth'].tolist(),
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
                        dataframe[c] = _data[c].iloc[0]

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
            crossover_radius=200000,
            min_depth=0,
    ):

        data_type_name = data.models.DataTypeName.objects.get(pk=parameter_id)
        cache_key = "get_profiles_stats-{}-{}-{}-{}-{}-{}-{}".format(
            self.id,
            parameter_id,
            hash(tuple(stations)),
            hash(tuple(xover_stations)),
            crossover_radius,
            min_depth,
            data_type_name.data_type.offset_type.id,
        )
        value = cache.get(cache_key, False)
        if value is not False:
            return value

        current_stations = self.get_interp_profiles(
            stations,
            parameter_id,
            min_depth=min_depth,
        )
        reference_stations = self.get_interp_profiles(
            xover_stations,
            parameter_id,
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

    def get_merge_data(
        self,
        primary_parameter,
        secondary_parameter,
        min_depth = 0,
    ):
        s1 = self.get_stations(
            parameter_id=primary_parameter
        )
        s2 = self.get_stations(
            parameter_id=secondary_parameter
        )
        stations = set(s1) and set(s2)
        primary = self.get_profiles_data(
            stations,
            primary_parameter,
            min_depth = min_depth,
            only_this_parameter = True,
        )
        secondary = self.get_profiles_data(
            stations,
            secondary_parameter,
            min_depth = min_depth,
            only_this_parameter = True,
        )
        merged = primary.merge(
            secondary[['depth_id','param']],
            how = 'inner',
            left_on = ['depth_id'],
            right_on = ['depth_id'],
            suffixes = ('_pri', '_sec'),
        )
        merged['diff'] = merged['param_pri'] - merged['param_sec']
        merged.rename(
            columns={'param_pri':'primary', 'param_sec': 'secondary'},
            inplace=True,
        )

        return merged
