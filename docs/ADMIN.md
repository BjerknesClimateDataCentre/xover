
Accessing the services
----------------------

The service supports using the standard Django admin interface for managing
data. This is accessed at http://localhost:8001/admin (`localhost:8001` is just the
dev server, and could be different for you). To set up a superuser
for the admin interface can be done using `python manage.py createsuperuser`
on the command line when in the d2qc/ folder.

API access is found at the /data - endpoint. Adding format=json as
GET - attributes returns raw pure json, otherwise data is presented in a
human readable format, using Django rest frameworks standard setup.

The API is still experimental, but currently supports

Get join data set:
    http://localhost:8001/data/join/dataset/{data_set_id}/[original_label,original_label,...]
    Example: http://localhost:8001/data/join/dataset/724/CTDTMP,SALNTY

Return data on the form:

    {
        expocode: "74DI20110715",
        id: 724,
        data_columns: [
            "id",
            "latitude",
            "longitude",
            "depth",
            "unix_time_millis",
            "CTDTMP_value",
            "SALNTY_value"
        ],
        data_points: [
            [
                1541950,
                48.6499,
                -17.0256,
                604,
                1311078240,
                8.8719,
                35.345
            ],
            [
                1541951,
                48.6499,
                -17.0256,
                604,
                1311078240,
                8.8763,
                35.3438
            ],
            ...
        ]
    }
