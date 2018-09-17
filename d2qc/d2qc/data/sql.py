import re
from django.db import connection

def get_data_set_data(data_set_ids=[0], types="", bounds=[], min_depth=0, max_depth=0):
    """
    Get data for a multiple datasets as a list of hierachical objects.

    Keyword args:
    data_set_ids -- The database id of the datasetself.
    types       -- Commaseparated string, data types from the data_types table.

    Example: get_data_set_data(724, "CTDTMP,SALNTY")

    Returns:
    [
        {
            id: 724,
            expocode: "74DI20110715",
            data_columns:
            [
                "id",
                "latitude",
                "longitude",
                "depth",
                "unix_time_millis",
                "CTDTMP_value",
                "SALNTY_value"
            ],
            data_points:
            [
                [
                    1542644,
                    28.782,
                    -16.0016,
                    2960,
                    1312418700,
                    2.7843,
                    34.9415
                ],
                [
                    1542645,
                    28.782,
                    -16.0016,
                    3459,
                    1312418700,
                    2.5308,
                    34.9148
                ],
                ...
            ],
        },
        {
            id: 725,
            ...
        },
        ...
    ]
    """

    cursor = connection.cursor()
    result = []
    select = """
        SELECT original_label, id from d2qc_datatypes where data_unit_id is not null
    """
    cursor.execute(select)
    typelist = dict([(type[0], type[1]) for type in cursor.fetchall()])

    select = """
        SELECT dp.data_set_id, ds.expocode, ds.min_lat, ds.max_lat,
        ds.min_lon, ds.max_lon, dp.id AS data_point_id,
        dp.latitude, dp.longitude, dp.depth, dp.unix_time_millis
    """
    frm = " FROM  d2qc_datasets ds"
    join = " INNER JOIN d2qc_datapoints dp ON (ds.id = dp.data_set_id)"
    ids = ','.join([str(i) for i in data_set_ids])
    where = " WHERE ds.id in (" + ids + ") "
    args = []
    if len(types) > 0:
        for type in types:
            px = re.sub('[^a-zA-Z0-9]', '', type)
            select += ", {}.value AS {}_value".format(px, px)
            join += " INNER JOIN d2qc_datavalues {}".format(px)
            join += " ON (dp.id = {}.data_point_id)".format(px)
            where += " AND {}.data_type_id = '{}'".format(px, typelist[type])
        if len(bounds) == 4:
            where += """
            AND dp.latitude between %s and %s
            AND dp.longitude between %s and %s
            """
            args.extend(bounds)
        if min_depth > 0:
            where += 'AND dp.depth > %s'
            args.append(min_depth)
        if max_depth > 0:
            where += 'AND dp.depth < %s'
            args.append(max_depth)



    order = " ORDER BY dp.data_set_id ASC, dp.unix_time_millis ASC, dp.depth ASC "
    cursor.execute(select + frm + join + where + order, args)

    data_set_id = -1
    data_points = []
    data_set = {}
    for row in cursor.fetchall():
        if row[0] != data_set_id:
            if data_set_id != -1:
                data_set['data_points'] = data_points
                data_points = []
                result.append(data_set)
            data_set = {}
            data_set['data_columns'] = [col[0] for col in cursor.description][6:]
            data_set['data_set_id'] = row[0]
            data_set['expocode'] = row[1]
            data_set['min_lat'] = row[2]
            data_set['max_lat'] = row[3]
            data_set['min_lon'] = row[4]
            data_set['max_lon'] = row[5]
            data_set_id = row[0]
        data_points.append(row[6:])

    if data_set_id != -1:
        data_set['data_points'] = data_points
        result.append(data_set)

    return result
