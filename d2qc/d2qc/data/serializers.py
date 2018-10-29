from d2qc.data.models import *
from rest_framework import serializers

# Serializers define the API representation.
class DataFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataFile
        fields = '__all__'

class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = '__all__'

class CastSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cast
        fields = '__all__'

class DepthSerializer(serializers.ModelSerializer):
    class Meta:
        model = Depth
        fields = '__all__'

class DataValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataValue
        fields = (
            'id',
            'data_point',
            'data_type',
            'value',
            'qc_flag',
            'qc2_flag',
        )

class NestedDataValueSerializer(DataValueSerializer):
    class Meta(DataValueSerializer.Meta):
        fields = (
            'id',
            'data_type',
            'value',
            'qc_flag',
            'qc2_flag',
        )

class DataSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSet
        fields = (
            'id',
            'expocode',
            'is_reference',
            'data_file',
        )

class NestedDataSetSerializer(serializers.ModelSerializer):
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
