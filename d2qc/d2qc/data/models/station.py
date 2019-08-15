from django.contrib.gis.db import models

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
