from django.contrib.gis.db import models

class OffsetType(models.Model):
    class Meta:
        db_table = 'd2qc_offset_types'
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20, default='', blank=True)
    description = models.CharField(max_length=255, default='', blank=True)
    def __str__(self):
        return self.name
