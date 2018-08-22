from d2qc.data.models import DataSet, DataType, DataPoint, DataValue, DataUnit
from rest_framework import serializers

# Serializers define the API representation.
class DataSetSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataSet
        fields = (
            'id',
            'expocode',
            'is_reference'
        )

class DataTypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataType
        fields = (
            'id',
            'identifier',
            'prefLabel',
            'altLabel',
            'definition',
            'original_label',
            'data_unit'
        )

class DataPointSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataPoint
        fields = (
            'id',
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
        fields = (
            'id',
            'data_point',
            'data_type',
            'value'
        )

class DataUnitSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataUnit
        fields = (
            'id',
            'identifier',
            'prefLabel',
            'altLabel',
            'definition'
        )
