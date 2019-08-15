from django.contrib.gis.db import models

class Cast(models.Model):
    class Meta:
        db_table = 'd2qc_casts'

    id = models.AutoField(primary_key=True)
    station = models.ForeignKey('Station',
            related_name='casts', on_delete=models.CASCADE)
    cast = models.IntegerField(null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
