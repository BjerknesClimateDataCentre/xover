from django.contrib.gis.db import models

class DataTypeName(models.Model):
    class Meta:
        db_table = 'd2qc_data_type_names'

    id = models.AutoField(primary_key=True)
    data_type = models.ForeignKey(
        'DataType',
        related_name = 'data_type_names',
        on_delete = models.CASCADE,
    )
    name = models.CharField(max_length=255)
    is_reference = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)
