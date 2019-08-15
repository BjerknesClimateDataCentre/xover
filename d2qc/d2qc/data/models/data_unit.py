from django.contrib.gis.db import models

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
