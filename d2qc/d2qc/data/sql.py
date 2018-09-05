import re
from django.db import connection

def getDataSetData(data_set_id=0, types=""):
    """
    Get data for a single dataset as a hierachical object.

    Keyword args:
    data_set_id -- The database id of the datasetself.
    types       -- Commaseparated string, data types from the data_types table.

    Example: getDataSetData(724, "CTDTMP,SALNTY")

    Returns:
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
    }
    """

    cursor = connection.cursor()
    cursor.execute('SELECT ds.id, ds.expocode FROM d2qc_datasets ds WHERE id=%s', [data_set_id])
    columns = [col[0] for col in cursor.description]
    result = dict(zip(columns, cursor.fetchone()))

    sql = "SELECT dp.id, dp.latitude, dp.longitude, dp.depth"
    sql += ", dp.unix_time_millis"
    frm = " FROM d2qc_datapoints dp "
    join = ""
    where = " WHERE dp.data_set_id = %s"
    if len(types) > 0:
        for type in types:
            px = re.sub('[^a-zA-Z0-9]', '', type)
            sql   += ", {}.value AS {}_value".format(px, px)
            join  += " INNER JOIN d2qc_datavalues {}".format(px)
            join  += " ON (dp.id = {}.data_point_id)".format(px)
            join  += " INNER JOIN d2qc_datatypes dt_{}".format(px)
            join  += " ON (dt_{}.id = {}.data_type_id)".format(px, px)
            where += " AND dt_{}.original_label = '{}'".format(px, type)
    order = " ORDER BY dp.unix_time_millis ASC, dp.depth ASC "
    cursor.execute(sql + frm + join + where + order, [data_set_id])
    result['data_columns'] = [col[0] for col in cursor.description]
    result['data_points'] = cursor.fetchall()
    return result
