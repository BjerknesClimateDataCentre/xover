from django.db import models
from django.forms import ModelForm


class DataSet(models.Model):
    class Meta:
        db_table = 'd2qc_datasets'
    id = models.AutoField(primary_key=True)
    expocode = models.CharField(max_length=255)
    is_reference = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

class DataSetForm(ModelForm):
    class Meta:
        model = DataSet
        fields = ['expocode']

class DataType(models.Model):
    class Meta:
        db_table = 'd2qc_datatypes'
        unique_together = ('identifier', 'original_label')
    id = models.AutoField(primary_key=True)
    data_unit = models.ForeignKey(
        'DataUnit',
        on_delete = models.CASCADE,
        blank = True,
        null = True,
    )
    identifier = models.CharField(max_length=20, default='', blank=True)
    prefLabel = models.CharField(max_length=255, default='', blank=True)
    altLabel = models.CharField(max_length=255, default='', blank=True)
    definition = models.CharField(max_length=255, default='', blank=True)
    original_label = models.CharField(max_length=20, default='')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

class DataUnit(models.Model):
    class Meta:
        db_table = 'd2qc_dataunits'
    id = models.AutoField(primary_key=True)
    identifier = models.CharField(max_length=20, default='', blank=True)
    prefLabel = models.CharField(max_length=255, default='', blank=True)
    altLabel = models.CharField(max_length=255, default='', blank=True)
    definition = models.CharField(max_length=255, default='', blank=True)
    original_label = models.CharField(max_length=20, default='')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

class DataPoint(models.Model):
    class Meta:
        db_table = 'd2qc_datapoints'
    id = models.AutoField(primary_key=True)
    data_set = models.ForeignKey('DataSet', related_name='points', on_delete=models.CASCADE)
    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)
    depth = models.DecimalField(max_digits=8, decimal_places=3)
    unix_time_millis = models.BigIntegerField()
    station_number = models.IntegerField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

class DataValue(models.Model):
    class Meta:
        db_table = 'd2qc_datavalues'
    id = models.AutoField(primary_key=True)
    data_point = models.ForeignKey('DataPoint', related_name='values', on_delete=models.CASCADE)
    data_type = models.ForeignKey('DataType', on_delete=models.CASCADE)
    value = models.DecimalField(max_digits=19, decimal_places=10)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    def save(self, *args, **kwargs):
        if int(float(self.value)) != -999:
            super(DataValue, self).save(*args, **kwargs)
