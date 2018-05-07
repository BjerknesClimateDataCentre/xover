from d2qc.data.models import DataSet, DataType, DataPoint, DataValue
from rest_framework import serializers

# Serializers define the API representation.
class DataSetSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataSet
        fields = ('expocode', 'is_reference')

class DataTypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataType
        fields = ('name', 'unit', 'description')

class DataPointSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataPoint
        fields = (
            'data_set',
            'latitude',
            'longitude',
            'depth',
            'unix_time_millis',
            'station_number'
        )

class DataValueSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataValue
        fields = ('data_point', 'data_type', 'value')
