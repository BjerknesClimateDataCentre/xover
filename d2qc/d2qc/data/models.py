from django.db import models

class DataSet(models.Model):
    class Meta:
        db_table = 'datasets'
    id = models.AutoField(primary_key=True)
    expocode = models.CharField(max_length=255)

class DataType(models.Model):
    class Meta:
        db_table = 'datatypes'
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    unit = models.CharField(max_length=255)
    description = models.CharField(max_length=255)


class DataPoint(models.Model):
    class Meta:
        db_table = 'datapoints'
    id = models.AutoField(primary_key=True)
    data_set_id = models.ForeignKey('DataSet', on_delete=models.CASCADE)
    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)
    depth = models.DecimalField(max_digits=8, decimal_places=3)
    unix_time_millis = models.BigIntegerField()

class DataValue(models.Model):
    class Meta:
        db_table = 'datavalues'
    id = models.AutoField(primary_key=True)
    data_point_id = models.ForeignKey('DataPoint', on_delete=models.CASCADE)
    data_type_id = models.ForeignKey('DataType', on_delete=models.CASCADE)
    value = models.DecimalField(max_digits=19, decimal_places=10)
