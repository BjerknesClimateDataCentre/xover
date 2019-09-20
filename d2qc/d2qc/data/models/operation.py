from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField

class Operation(models.Model):
    class Meta:
        db_table = 'd2qc_operations'

    id = models.AutoField(primary_key=True)
    data_set = models.ForeignKey(
        'DataSet',
        related_name = 'operations',
        on_delete = models.CASCADE,
    )
    data_type_name = models.ForeignKey(
        'DataTypeName',
        related_name = 'operations',
        on_delete = models.CASCADE,
    )
    operation_type = models.ForeignKey(
        'OperationType',
        on_delete = models.CASCADE,
    )
    name = models.CharField(max_length=255)
    data = JSONField(null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)
