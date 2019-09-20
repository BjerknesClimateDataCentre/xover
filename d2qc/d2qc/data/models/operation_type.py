from django.contrib.gis.db import models

class OperationType(models.Model):
    class Meta:
        db_table = 'd2qc_operation_types'

    id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=20,
    )
    description = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)
