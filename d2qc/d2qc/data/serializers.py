from d2qc.data.models import DataSet, DataType, DataPoint, DataValue, DataUnit
from rest_framework import serializers

# Serializers define the API representation.
class DataValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataValue
        fields = (
            'id',
            'data_point',
            'data_type',
            'value'
        )
class NestedDataValueSerializer(DataValueSerializer):
    class Meta(DataValueSerializer.Meta):
        fields = (
            'id',
            'data_type',
            'value'
        )

class DataPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataPoint
        fields = (
            'id',
            'data_set',
            'latitude',
            'longitude',
            'depth',
            'unix_time_millis',
            'station_number',
        )
class NestedDataPointSerializer(serializers.ModelSerializer):
    values = NestedDataValueSerializer(read_only=True, many=True)
    class Meta:
        model = DataPoint
        fields = (
            'id',
            'latitude',
            'longitude',
            'depth',
            'unix_time_millis',
            'station_number',
            'values',
        )
class DataSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSet
        fields = (
            'id',
            'expocode',
            'is_reference',
        )

class NestedDataSetSerializer(serializers.ModelSerializer):
    points = NestedDataPointSerializer(read_only=True, many=True)
    class Meta:
        model = DataSet
        fields = (
            'id',
            'expocode',
            'is_reference',
            'points',
        )

class DataUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataUnit
        fields = (
            'id',
            'identifier',
            'prefLabel',
            'altLabel',
            'definition'
        )

class DataTypeSerializer(serializers.ModelSerializer):
    data_unit = DataUnitSerializer(read_only=True)
    class Meta:
        model = DataType
        fields = (
            'id',
            'identifier',
            'prefLabel',
            'altLabel',
            'definition',
            'original_label',
            'data_unit',
        )
