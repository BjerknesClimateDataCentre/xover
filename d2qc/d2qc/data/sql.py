import re
from django.db import connection

def get_data_set_data(data_set_ids=[0], types=[], bounds=[], min_depth=0, max_depth=0):
    """
    Get data for a multiple datasets as a list of hierachical objects.

    Keyword args:
    data_set_ids -- The database id of the datasetself.
    types       -- Commaseparated string, data types from the data_types table.

    Example: get_data_set_data(724, "CTDTMP,SALNTY")

    Returns:
    {
        data_columns:
        [
            "depth_id",
            "depth",
            "latitude",
            "longitude",
            "date_and_time",
            "temperature_value",
            "salinity_value",
        ],
        data_sets:
        [
            {
                dataset_id: 724,
                expocode: "74DI20110715",
                stations:
                [
                    {
                        station_id: 1234,
                        station_number: 12,
                        casts: [
                            {
                                "cast_id": 5678,
                                "cast_no": 1,
                                "depth_id": [
                                1234,
                                1235,
                                ...
                                ],
                                "depth": [
                                10.1,
                                20.5,
                                ...
                                ],
                                "date_and_time": [
                                "1985-01-01 20:00:00",
                                "1985-01-01 20:00:00",
                                ...
                                ],
                                "latitude": [
                                60.13,
                                61.10,
                                ...
                                ],
                                "longitude": [
                                10.10,
                                11.10,
                                ...
                                ],
                                "temperature_value": [
                                1.1432,
                                1.1333,
                                ...
                                ],
                                "salinity_value": [
                                35.4504,
                                35.4550,
                                ...
                                ],
                            },
                        ],
                    },
                ],
            },
            {
                data_set_id: 725,
                ...
            },
            ...
        ]
    }
    """

    cursor = connection.cursor()
    result = []
    select = """
        SELECT original_label, id from d2qc_data_types
    """
    cursor.execute(select)
    typelist = dict([(type[0], type[1]) for type in cursor.fetchall()])
    if not types:
            types.extend(['temperature'])

    select = """
        SELECT ds.id as data_set_id, ds.expocode,
        s.id as station_id, s.station_number,
        c.id as cast_id, c.cast as cast_no,
        d.id as depth_id, d.depth,
        d.date_and_time,
        st_y(s.position) as latitude, st_x(s.position) as longitude
    """
    frm = " FROM  d2qc_data_sets ds"
    join = " INNER JOIN d2qc_stations s ON (ds.id = s.data_set_id)"
    join += " INNER JOIN d2qc_casts c ON (s.id = c.station_id)"
    join += " INNER JOIN d2qc_depths d ON (c.id = d.cast_id)"
    ids = ','.join([str(i) for i in data_set_ids])
    where = " WHERE ds.id in (" + ids + ") "
    args = []
    not_all_nulls = []
    if len(types) > 0:
        for type in types:
            px = re.sub('[^a-zA-Z0-9]', '', type)
            select += ", {}.value AS {}_value".format(px, px)
            join += " LEFT OUTER JOIN d2qc_data_values {}".format(px)
            join += " ON (d.id = {}.depth_id".format(px)
            join += " AND {}.data_type_id = '{}')".format(px, typelist[type])
            not_all_nulls.append("{}.value".format(px))
        if len(bounds) == 4:
            where += """
            AND s.latitude between %s and %s
            AND s.longitude between %s and %s
            """
            args.extend(bounds)
        if min_depth > 0:
            where += 'AND d.depth > %s'
            args.append(min_depth)
        if max_depth > 0:
            where += 'AND d.depth < %s'
            args.append(max_depth)

    # Dont include if all values are null
    where += " AND ("
    where += ' IS NOT NULL OR '.join(not_all_nulls)
    where += ' IS NOT NULL'
    where += ")"


    order = " ORDER BY s.data_set_id ASC, s.id, c.id, d.id"
    cursor.execute(select + frm + join + where + order, args)

    data_set_id = ()
    station_id = ()
    cast_id = ()
    data = {}
    data_set = {}
    station = {}
    cast = {}
    output = {}
    output['data_columns'] = [col[0] for col in cursor.description][6:]
    output['data_sets'] = []
    for row in cursor.fetchall():
        if (row[0]) != data_set_id:
            if data_set_id:
                station['casts'].append(cast);
                data_set['stations'].append(station)
                output['data_sets'].append(data_set)
            data_set = {'stations':[]}
            station = {'casts':[]}
            station['station_id'] = row[2]
            station['station_number'] = row[3]
            cast = {}
            cast['cast_id'] = row[4]
            cast['cast_no'] = row[5]
            data_set['data_set_id'] = row[0]
            data_set['expocode'] = row[1]
            data_set_id = (row[0])
            station_id = (row[0], row[2])
            cast_id = (row[0], row[2], row[4])
        elif (row[0], row[2]) != station_id:
            if station_id:
                station['casts'].append(cast);
                data_set['stations'].append(station)
            cast = {}
            cast['cast_id'] = row[4]
            cast['cast_no'] = row[5]
            station = {'casts':[]}
            station['station_id'] = row[2]
            station['station_number'] = row[3]
            station_id = (row[0], row[2])
            cast_id = (row[0], row[2], row[4])
        elif (row[0], row[2], row[4]) != cast_id:
            if cast_id:
                station['casts'].append(cast);
            cast = {}
            cast['cast_id'] = row[4]
            cast['cast_no'] = row[5]
            cast_id = (row[0], row[2], row[4])
        for i, v in enumerate(row[6:]):
            if not output['data_columns'][i] in cast:
                cast[output['data_columns'][i]] = []
            cast[output['data_columns'][i]].append(v)

    if data_set_id:
        station['casts'].append(cast);
        data_set['stations'].append(station)
        output['data_sets'].append(data_set)

    return output

def dataset_extends(data_set_id, min_depth = 0):
    cursor = connection.cursor()
    select = """
            SELECT
            st_ymin(st_extent(position)), st_ymax(st_extent(position)),
            st_xmin(st_extent(position)), st_xmax(st_extent(position))
            FROM d2qc_stations s
    """
    args = []
    where = ' where data_set_id = %s '
    args.append(data_set_id)

    join = ''
    if min_depth > 0:
        join = " INNER JOIN d2qc_casts c on (c.station_id = s.id) "
        join += " INNER JOIN d2qc_depths d on (c.id = d.cast_id) "
        where += ' AND d.depth > %s'
        args.append(min_depth)
    print(select + join + where + " limit 5;")
    cursor.execute(select + join + where, args)
    return cursor.fetchone()
